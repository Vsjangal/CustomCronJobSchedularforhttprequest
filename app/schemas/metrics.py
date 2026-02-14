from pydantic import BaseModel


class ScheduleMetrics(BaseModel):
    """Aggregated metrics for a single schedule."""

    schedule_id: str
    total_runs: int
    success_count: int
    failure_count: int
    avg_latency_ms: float | None = None
    last_run_at: str | None = None


class MetricsResponse(BaseModel):
    """Top-level metrics aggregation across all schedules."""

    total_schedules: int
    active_schedules: int
    paused_schedules: int
    total_runs: int
    total_success: int
    total_failures: int
    avg_latency_ms: float | None = None
    schedules: list[ScheduleMetrics] = []
