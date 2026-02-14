from datetime import datetime

from pydantic import BaseModel


class AttemptResponse(BaseModel):
    """Schema for a single HTTP request attempt."""

    id: str
    run_id: str
    attempt_number: int
    status_code: int | None = None
    latency_ms: float | None = None
    response_size_bytes: int | None = None
    error_type: str | None = None
    error_message: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    """Schema for Run list responses (without attempts)."""

    id: str
    schedule_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RunDetailResponse(RunResponse):
    """Schema for a single Run with its full attempt history."""

    attempts: list[AttemptResponse] = []
