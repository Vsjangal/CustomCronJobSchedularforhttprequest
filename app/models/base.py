import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def generate_uuid() -> str:
    """Generate a new UUID4 string for use as a primary key."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (no tzinfo)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
