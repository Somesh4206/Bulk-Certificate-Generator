"""Background job processing: one PDF per recipient, failure-isolated."""
import logging
from datetime import datetime

from app.database import SessionLocal
from app.models.certificate import Certificate
from app.models.job import GenerationJob
from app.services.certificate_generator import (
    build_certificate_path,
    render_certificate,
)

logger = logging.getLogger(__name__)


def process_job(job_id: str) -> None:
    """Run in FastAPI BackgroundTasks. Never lets one bad cert stop the rest."""
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if job is None:
            logger.error("Job %s not found in background worker", job_id)
            return

        job.status = "processing"
        db.commit()

        certs = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.id)
            .all()
        )
        date_str = job.certificate_date.strftime("%d %B %Y")

        success = 0
        failed = 0
        for cert in certs:
            cert.status = "processing"
            db.commit()
            try:
                # Simulated per-recipient failure hook (used by tests to prove
                # isolation). Any name starting with FAIL_ fails on purpose.
                if cert.recipient_name.startswith("FAIL_"):
                    raise ValueError("Simulated generation failure for testing")

                path = build_certificate_path(job_id, cert.id)
                render_certificate(
                    path,
                    cert.recipient_name,
                    job.certificate_title,
                    job.event_name,
                    date_str,
                )
                cert.status = "success"
                cert.file_path = str(path)
                cert.error_message = None
                success += 1
            except Exception as exc:  # per-certificate isolation
                logger.exception(
                    "Certificate %s failed (job %s)", cert.id, job_id
                )
                cert.status = "failed"
                cert.error_message = str(exc)[:500]
                cert.file_path = None
                failed += 1
            db.commit()

        job.success_count = success
        job.failed_count = failed
        job.completed_at = datetime.utcnow()
        if failed == 0 and success > 0:
            job.status = "completed"
        elif success > 0:
            job.status = "completed_with_errors"
        elif failed > 0:
            # Every certificate failed, but the job itself ran.
            job.status = "completed_with_errors"
        else:
            job.status = "failed"
        db.commit()
    except Exception:
        logger.exception("Job %s crashed", job_id)
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job is not None:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()
