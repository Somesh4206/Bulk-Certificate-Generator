"""Pydantic schemas for jobs."""
from datetime import date as date_type
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class RecipientCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Recipient full name")
    email: EmailStr = Field(..., description="Recipient email address")


class JobCreateRequest(BaseModel):
    certificate_title: str = Field(..., min_length=1)
    event_name: str = Field(..., min_length=1)
    date: date_type = Field(..., description="Certificate date, YYYY-MM-DD")
    recipients: List[RecipientCreate] = Field(..., min_length=1)


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    total: int


class CertificateInfo(BaseModel):
    id: int
    recipient_name: str
    status: str
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    total: int
    successful: int
    failed: int
    certificates: List[CertificateInfo]
