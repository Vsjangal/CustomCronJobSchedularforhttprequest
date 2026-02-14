import enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid, utcnow


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class ErrorType(str, enum.Enum):
    TIMEOUT = "timeout"
    DNS = "dns"
    CONNECTION = "connection"
    HTTP_4XX = "http_4xx"
    HTTP_5XX = "http_5xx"
    UNKNOWN = "unknown"


class Run(Base):
    """A single scheduled execution. Contains one or more Attempts."""

    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    schedule_id = Column(String, ForeignKey("schedules.id"), nullable=False)
    status = Column(String, nullable=False, default=RunStatus.PENDING.value)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    schedule = relationship("Schedule", back_populates="runs")
    attempts = relationship(
        "Attempt",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="Attempt.attempt_number",
    )


class Attempt(Base):
    """A single HTTP request attempt within a Run (supports retries)."""

    __tablename__ = "attempts"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    error_type = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    run = relationship("Run", back_populates="attempts")
