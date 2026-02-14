from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from app.models.schedule import ScheduleType


class ScheduleCreate(BaseModel):
    """Schema for creating a new Schedule."""

    target_id: str
    schedule_type: ScheduleType
    interval_seconds: int
    duration_seconds: int | None = None
    max_retries: int = 0
    request_timeout_seconds: int = 30

    @field_validator("interval_seconds")
    @classmethod
    def validate_interval_is_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("interval_seconds must be at least 1")
        return value

    @field_validator("request_timeout_seconds")
    @classmethod
    def validate_timeout_is_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("request_timeout_seconds must be at least 1")
        return value

    @model_validator(mode="after")
    def validate_window_requires_duration(self) -> "ScheduleCreate":
        if self.schedule_type == ScheduleType.WINDOW and self.duration_seconds is None:
            raise ValueError("duration_seconds is required for window schedules")
        return self


class ScheduleResponse(BaseModel):
    """Schema for Schedule API responses."""

    id: str
    target_id: str
    schedule_type: str
    interval_seconds: int
    duration_seconds: int | None = None
    status: str
    started_at: datetime | None = None
    expires_at: datetime | None = None
    last_run_at: datetime | None = None
    max_retries: int
    request_timeout_seconds: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
