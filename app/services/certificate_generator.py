"""Thin wrapper: safe file paths + call the predefined template."""
import os
from pathlib import Path


def get_cert_base_dir() -> Path:
    return Path(os.getenv("CERT_OUTPUT_DIR", "generated_certificates"))


def build_certificate_path(job_id: str, certificate_id: int) -> Path:
    """Build a safe path. Never uses user input as path components.

    job_id comes from our own UUID; certificate_id is an integer PK.
    """
    base = get_cert_base_dir()
    job_dir = base / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir / f"certificate_{int(certificate_id)}.pdf"


def render_certificate(
    output_path: Path,
    recipient_name: str,
    certificate_title: str,
    event_name: str,
    date_str: str,
) -> None:
    # Import here so tests can run without reportlab until installed.
    from templates.certificate_template import generate_certificate_pdf

    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_certificate_pdf(
        str(output_path), recipient_name, certificate_title, event_name, date_str
    )
