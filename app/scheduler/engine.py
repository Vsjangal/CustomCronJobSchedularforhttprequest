"""
Polling-based async scheduler engine.

Every tick (default 1 s) the engine:
  1. Loads all active schedules from the DB.
  2. Expires window-type schedules whose duration has elapsed.
  3. Determines which schedules are "due" (next_run_at <= now).
  4. Dispatches an async execution task for each due schedule.

Duplicate-prevention: an in-memory set tracks schedule IDs that are
currently executing.  A schedule cannot be dispatched again until the
previous execution completes.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from app.models.run import RunStatus
from app.models.schedule import Schedule, ScheduleStatus, ScheduleType
from app.services import run_service
from app.services.http_executor import execute_http_request

logger = logging.getLogger(__name__)


class SchedulerEngine:
    """Async background scheduler that polls the DB for due schedules."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self._running = False
        self._task: asyncio.Task | None = None
        self._active_executions: set[str] = set()
        self._poll_interval: float = 1.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Begin the background polling loop."""
        logger.info("Scheduler engine starting")
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Signal the loop to stop and wait for it to finish."""
        logger.info("Scheduler engine stopping")
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    # ------------------------------------------------------------------
    # Core loop
    # ------------------------------------------------------------------

    async def _run_loop(self) -> None:
        """Infinite loop that calls _tick once per poll interval."""
        while self._running:
            try:
                await self._tick()
            except Exception:
                logger.exception("Error in scheduler tick")
            await asyncio.sleep(self._poll_interval)

    async def _tick(self) -> None:
        """Single iteration: expire windows, find due, dispatch."""
        async with self._session_factory() as session:
            now = _utcnow()
            active_schedules = await self._load_active_schedules(session)
            self._mark_expired_windows(active_schedules, now)
            due_schedules = self._filter_due(active_schedules, now)
            self._dispatch(due_schedules, now)
            await session.commit()

    # ------------------------------------------------------------------
    # Schedule loading & filtering
    # ------------------------------------------------------------------

    async def _load_active_schedules(
        self, session: AsyncSession
    ) -> list[Schedule]:
        """Fetch all active schedules with targets eagerly loaded."""
        stmt = (
            select(Schedule)
            .where(Schedule.status == ScheduleStatus.ACTIVE.value)
            .options(joinedload(Schedule.target))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    def _mark_expired_windows(
        self, schedules: list[Schedule], now: datetime
    ) -> None:
        """Transition any window schedule past its expiry to COMPLETED."""
        for schedule in schedules:
            if self._is_window_expired(schedule, now):
                schedule.status = ScheduleStatus.COMPLETED.value
                logger.info("Window schedule %s completed", schedule.id)

    def _is_window_expired(self, schedule: Schedule, now: datetime) -> bool:
        """Check whether a window-type schedule has exceeded its duration."""
        return (
            schedule.schedule_type == ScheduleType.WINDOW.value
            and schedule.expires_at is not None
            and now >= schedule.expires_at
        )

    def _filter_due(
        self, schedules: list[Schedule], now: datetime
    ) -> list[Schedule]:
        """Return only schedules that are due to fire right now."""
        return [
            s for s in schedules
            if s.status == ScheduleStatus.ACTIVE.value and self._is_due(s, now)
        ]

    def _is_due(self, schedule: Schedule, now: datetime) -> bool:
        """True if the schedule should execute at *now*."""
        if schedule.id in self._active_executions:
            return False
        if schedule.last_run_at is None:
            return True
        next_run = schedule.last_run_at + timedelta(
            seconds=schedule.interval_seconds
        )
        return now >= next_run

    # ------------------------------------------------------------------
    # Dispatch & execution
    # ------------------------------------------------------------------

    def _dispatch(self, schedules: list[Schedule], now: datetime) -> None:
        """Kick off an async task for each due schedule."""
        for schedule in schedules:
            schedule.last_run_at = now
            self._active_executions.add(schedule.id)
            asyncio.create_task(self._execute_safe(schedule.id))
            logger.info("Dispatched schedule %s", schedule.id)

    async def _execute_safe(self, schedule_id: str) -> None:
        """Wrapper that guarantees the active-set is cleaned up."""
        try:
            await self._execute(schedule_id)
        except Exception:
            logger.exception("Execution failed for schedule %s", schedule_id)
        finally:
            self._active_executions.discard(schedule_id)

    async def _execute(self, schedule_id: str) -> None:
        """Load the schedule, create a Run, fire requests, record results."""
        async with self._session_factory() as session:
            schedule = await self._load_schedule_with_target(
                session, schedule_id
            )
            if not schedule or not schedule.target:
                logger.warning("Schedule %s or target missing", schedule_id)
                return

            run = await run_service.create_run(session, schedule_id)
            try:
                status = await self._execute_with_retries(session, schedule, run)
            except Exception:
                logger.exception("Unexpected error in schedule %s", schedule_id)
                status = RunStatus.FAILED
            await run_service.complete_run(session, run, status)
            await session.commit()

    async def _load_schedule_with_target(
        self, session: AsyncSession, schedule_id: str
    ) -> Schedule | None:
        """Fetch a schedule by ID with its target eagerly loaded."""
        stmt = (
            select(Schedule)
            .where(Schedule.id == schedule_id)
            .options(joinedload(Schedule.target))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def _execute_with_retries(
        self, session: AsyncSession, schedule: Schedule, run
    ) -> RunStatus:
        """Try the request up to (max_retries + 1) times."""
        target = schedule.target
        max_attempts = schedule.max_retries + 1

        for attempt_num in range(1, max_attempts + 1):
            attempt = await execute_http_request(
                url=target.url,
                method=target.method,
                headers=target.headers,
                body=target.body_template,
                timeout_seconds=schedule.request_timeout_seconds,
            )
            attempt.run_id = run.id
            attempt.attempt_number = attempt_num
            await run_service.add_attempt(session, attempt)

            if attempt.error_type is None:
                return RunStatus.SUCCESS

        return RunStatus.FAILED


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    """Naive UTC now, consistent with model helpers."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
