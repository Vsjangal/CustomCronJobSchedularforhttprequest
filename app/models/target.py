from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid, utcnow


class Target(Base):
    """Represents an HTTP endpoint to send scheduled requests to."""

    __tablename__ = "targets"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    method = Column(String, nullable=False, default="GET")
    headers = Column(JSON, nullable=True, default=dict)
    body_template = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    schedules = relationship(
        "Schedule", back_populates="target", cascade="all, delete-orphan"
    )
