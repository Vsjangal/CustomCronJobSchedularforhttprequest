"""REST endpoints for Schedule lifecycle management."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.schedule import ScheduleStatus
from app.schemas.schedule import ScheduleCreate, ScheduleResponse
from app.services import schedule_service, target_service

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    data: ScheduleCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new schedule for an existing target."""
    target = await target_service.get_target(session, data.target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return await schedule_service.create_schedule(session, data)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(session: AsyncSession = Depends(get_session)):
    """List all schedules."""
    return await schedule_service.list_schedules(session)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a single schedule by ID."""
    schedule = await schedule_service.get_schedule(session, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.post("/{schedule_id}/pause", response_model=ScheduleResponse)
async def pause_schedule(
    schedule_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Pause an active schedule. Only active schedules can be paused."""
    schedule = await _get_schedule_or_404(session, schedule_id)
    if schedule.status != ScheduleStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400, detail="Only active schedules can be paused"
        )
    return await schedule_service.pause_schedule(session, schedule)


@router.post("/{schedule_id}/resume", response_model=ScheduleResponse)
async def resume_schedule(
    schedule_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Resume a paused schedule. Only paused schedules can be resumed."""
    schedule = await _get_schedule_or_404(session, schedule_id)
    if schedule.status != ScheduleStatus.PAUSED.value:
        raise HTTPException(
            status_code=400, detail="Only paused schedules can be resumed"
        )
    return await schedule_service.resume_schedule(session, schedule)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a schedule and all its runs."""
    schedule = await _get_schedule_or_404(session, schedule_id)
    await schedule_service.delete_schedule(session, schedule)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_schedule_or_404(session: AsyncSession, schedule_id: str):
    """Fetch a schedule or raise 404."""
    schedule = await schedule_service.get_schedule(session, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule
