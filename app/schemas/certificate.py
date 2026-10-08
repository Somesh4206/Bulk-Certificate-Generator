"""Pydantic schemas for certificates (kept minimal)."""
from pydantic import BaseModel


class CertificateResponse(BaseModel):
    id: int
    job_id: str
    recipient_name: str
    status: str
