"""API routes: POST job, GET job status, GET certificate PDF."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models.certificate import Certificate
from app.models.job import GenerationJob
from app.schemas.job import (
    CertificateInfo,
    JobCreateRequest,
    JobCreateResponse,
    JobStatusResponse,
)
from app.services.job_service import process_job

router = APIRouter()


@router.post(
    "/jobs", response_model=JobCreateResponse, status_code=202, summary="Create bulk job"
)
def create_job(payload: JobCreateRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    """Validate, store job + pending certificates, return immediately."""
    job = GenerationJob(
        certificate_title=payload.certificate_title.strip(),
        event_name=payload.event_name.strip(),
        certificate_date=payload.date,
        status="queued",
        total_count=len(payload.recipients),
    )
    db.add(job)
    db.flush()  # assign job.id before adding children

    for r in payload.recipients:
        db.add(
            Certificate(
                job_id=job.id,
                recipient_name=r.name.strip(),
                recipient_email=str(r.email),
                status="pending",
            )
        )
    db.commit()
    db.refresh(job)

    bg.add_task(process_job, job.id)
    return JobCreateResponse(job_id=job.id, status="queued", total=job.total_count)


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status and progress",
)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    certs = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .order_by(Certificate.id)
        .all()
    )
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        total=job.total_count,
        successful=job.success_count,
        failed=job.failed_count,
        certificates=[
            CertificateInfo(
                id=c.id,
                recipient_name=c.recipient_name,
                status=c.status,
                error=c.error_message,
            )
            for c in certs
        ],
    )


@router.get(
    "/certificates/{certificate_id}",
    summary="Download generated certificate PDF",
    response_class=FileResponse,
)
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if cert.status != "success" or not cert.file_path:
        raise HTTPException(
            status_code=422,
            detail=f"Certificate not ready: status={cert.status}",
        )
    if not os.path.isfile(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate file missing")
    filename = f"certificate_{cert.id}.pdf"
    return FileResponse(
        cert.file_path, media_type="application/pdf", filename=filename
    )
