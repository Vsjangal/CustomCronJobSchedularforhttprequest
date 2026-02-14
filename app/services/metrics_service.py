"""Metrics aggregation across schedules and runs."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Attempt, Run, RunStatus
from app.models.schedule import Schedule, ScheduleStatus
from app.schemas.metrics import MetricsResponse, ScheduleMetrics


async def get_metrics(session: AsyncSession) -> MetricsResponse:
    """Build a full metrics snapshot for all schedules and runs."""
    schedule_counts = await _count_schedules(session)
    run_counts = await _count_runs(session)
    avg_latency = await _avg_latency_all(session)
    per_schedule = await _per_schedule_metrics(session)

    return MetricsResponse(
        total_schedules=schedule_counts["total"],
        active_schedules=schedule_counts["active"],
        paused_schedules=schedule_counts["paused"],
        total_runs=run_counts["total"],
        total_success=run_counts["success"],
        total_failures=run_counts["failure"],
        avg_latency_ms=avg_latency,
        schedules=per_schedule,
    )


async def _count_schedules(session: AsyncSession) -> dict:
    """Count total, active, and paused schedules."""
    total = await session.scalar(select(func.count(Schedule.id))) or 0
    active = await session.scalar(
        select(func.count(Schedule.id)).where(
            Schedule.status == ScheduleStatus.ACTIVE.value
        )
    ) or 0
    paused = await session.scalar(
        select(func.count(Schedule.id)).where(
            Schedule.status == ScheduleStatus.PAUSED.value
        )
    ) or 0
    return {"total": total, "active": active, "paused": paused}


async def _count_runs(session: AsyncSession) -> dict:
    """Count total, successful, and failed runs."""
    total = await session.scalar(select(func.count(Run.id))) or 0
    success = await session.scalar(
        select(func.count(Run.id)).where(
            Run.status == RunStatus.SUCCESS.value
        )
    ) or 0
    failure = await session.scalar(
        select(func.count(Run.id)).where(
            Run.status == RunStatus.FAILED.value
        )
    ) or 0
    return {"total": total, "success": success, "failure": failure}


async def _avg_latency_all(session: AsyncSession) -> float | None:
    """Average latency across all attempts."""
    result = await session.scalar(select(func.avg(Attempt.latency_ms)))
    return round(result, 2) if result else None


async def _per_schedule_metrics(session: AsyncSession) -> list[ScheduleMetrics]:
    """Compute metrics per schedule."""
    result = await session.execute(select(Schedule))
    schedules = result.scalars().all()
    return [await _single_schedule_metrics(session, s) for s in schedules]


async def _single_schedule_metrics(
    session: AsyncSession, schedule: Schedule
) -> ScheduleMetrics:
    """Aggregate run/attempt stats for one schedule."""
    total = await session.scalar(
        select(func.count(Run.id)).where(Run.schedule_id == schedule.id)
    ) or 0
    success = await session.scalar(
        select(func.count(Run.id)).where(
            Run.schedule_id == schedule.id,
            Run.status == RunStatus.SUCCESS.value,
        )
    ) or 0
    avg_lat = await _avg_latency_for_schedule(session, schedule.id)

    return ScheduleMetrics(
        schedule_id=schedule.id,
        total_runs=total,
        success_count=success,
        failure_count=total - success,
        avg_latency_ms=avg_lat,
        last_run_at=str(schedule.last_run_at) if schedule.last_run_at else None,
    )


async def _avg_latency_for_schedule(
    session: AsyncSession, schedule_id: str
) -> float | None:
    """Average attempt latency for a specific schedule."""
    result = await session.scalar(
        select(func.avg(Attempt.latency_ms)).where(
            Attempt.run_id.in_(
                select(Run.id).where(Run.schedule_id == schedule_id)
            )
        )
    )
    return round(result, 2) if result else None
