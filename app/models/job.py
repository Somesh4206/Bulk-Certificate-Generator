"""generation_jobs table: one row per bulk request."""
import uuid
from datetime import datetime
from sqlalchemy import Column, Date, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def _new_id() -> str:
    return uuid.uuid4().hex


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String, primary_key=True, default=_new_id)
    certificate_title = Column(String, nullable=False)
    event_name = Column(String, nullable=False)
    certificate_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="queued")
    total_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    certificates = relationship(
        "Certificate", back_populates="job", cascade="all, delete-orphan"
    )
