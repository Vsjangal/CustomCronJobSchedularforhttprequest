import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid, utcnow


class ScheduleType(str, enum.Enum):
    INTERVAL = "interval"
    WINDOW = "window"


class ScheduleStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Schedule(Base):
    """Defines when and how often to fire requests against a Target."""

    __tablename__ = "schedules"

    id = Column(String, primary_key=True, default=generate_uuid)
    target_id = Column(String, ForeignKey("targets.id"), nullable=False)
    schedule_type = Column(String, nullable=False)
    interval_seconds = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default=ScheduleStatus.ACTIVE.value)
    started_at = Column(DateTime, default=utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    max_retries = Column(Integer, default=0)
    request_timeout_seconds = Column(Integer, default=30)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    target = relationship("Target", back_populates="schedules")
    runs = relationship(
        "Run", back_populates="schedule", cascade="all, delete-orphan"
    )
