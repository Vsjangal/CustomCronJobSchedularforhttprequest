"""Operations for Run and Attempt entities."""

from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.run import Attempt, Run, RunStatus


async def create_run(session: AsyncSession, schedule_id: str) -> Run:
    """Create a new pending Run for the given schedule."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    run = Run(
        schedule_id=schedule_id,
        status=RunStatus.PENDING.value,
        started_at=now,
    )
    session.add(run)
    await session.flush()
    return run


async def complete_run(
    session: AsyncSession, run: Run, status: RunStatus
) -> Run:
    """Mark a Run as completed with the final status."""
    run.status = status.value
    run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.flush()
    return run


async def add_attempt(session: AsyncSession, attempt: Attempt) -> Attempt:
    """Persist a new attempt record within the current transaction."""
    session.add(attempt)
    await session.flush()
    return attempt


async def list_runs(
    session: AsyncSession,
    schedule_id: str | None = None,
    status: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Run]:
    """Query runs with optional filters, pagination, and ordering."""
    stmt = select(Run)
    filters = _build_run_filters(schedule_id, status, start_time, end_time)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(Run.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _build_run_filters(
    schedule_id: str | None,
    status: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
) -> list:
    """Build a list of SQLAlchemy filter expressions from query params."""
    filters: list = []
    if schedule_id:
        filters.append(Run.schedule_id == schedule_id)
    if status:
        filters.append(Run.status == status)
    if start_time:
        filters.append(Run.started_at >= start_time)
    if end_time:
        filters.append(Run.started_at <= end_time)
    return filters


async def get_run_with_attempts(
    session: AsyncSession, run_id: str
) -> Run | None:
    """Fetch a single run with its attempts eagerly loaded."""
    stmt = (
        select(Run)
        .where(Run.id == run_id)
        .options(joinedload(Run.attempts))
    )
    result = await session.execute(stmt)
    return result.scalars().first()
