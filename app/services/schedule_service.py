"""CRUD and lifecycle operations for Schedule entities."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.schedule import Schedule, ScheduleStatus, ScheduleType
from app.schemas.schedule import ScheduleCreate


async def create_schedule(session: AsyncSession, data: ScheduleCreate) -> Schedule:
    """Create a new Schedule. If it's a window type, compute its expiry."""
    schedule = Schedule(
        target_id=data.target_id,
        schedule_type=data.schedule_type.value,
        interval_seconds=data.interval_seconds,
        duration_seconds=data.duration_seconds,
        status=ScheduleStatus.ACTIVE.value,
        max_retries=data.max_retries,
        request_timeout_seconds=data.request_timeout_seconds,
    )
    _set_expiration_for_window(schedule, data)
    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)
    return schedule


def _set_expiration_for_window(schedule: Schedule, data: ScheduleCreate) -> None:
    """Set started_at and expires_at when the schedule is a window type."""
    if data.schedule_type != ScheduleType.WINDOW or not data.duration_seconds:
        return
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    schedule.started_at = now
    schedule.expires_at = now + timedelta(seconds=data.duration_seconds)


async def list_schedules(session: AsyncSession) -> list[Schedule]:
    """Return all schedules ordered by most recently created."""
    stmt = select(Schedule).order_by(Schedule.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_schedule(session: AsyncSession, schedule_id: str) -> Schedule | None:
    """Fetch a single schedule by ID."""
    return await session.get(Schedule, schedule_id)


async def pause_schedule(session: AsyncSession, schedule: Schedule) -> Schedule:
    """Transition a schedule from active to paused."""
    schedule.status = ScheduleStatus.PAUSED.value
    await session.commit()
    await session.refresh(schedule)
    return schedule


async def resume_schedule(session: AsyncSession, schedule: Schedule) -> Schedule:
    """Transition a schedule from paused back to active."""
    schedule.status = ScheduleStatus.ACTIVE.value
    await session.commit()
    await session.refresh(schedule)
    return schedule


async def delete_schedule(session: AsyncSession, schedule: Schedule) -> None:
    """Remove a schedule and cascade-delete its runs."""
    await session.delete(schedule)
    await session.commit()


async def get_active_schedules_with_targets(
    session: AsyncSession,
) -> list[Schedule]:
    """Load all active schedules with their targets eagerly loaded."""
    stmt = (
        select(Schedule)
        .where(Schedule.status == ScheduleStatus.ACTIVE.value)
        .options(joinedload(Schedule.target))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
