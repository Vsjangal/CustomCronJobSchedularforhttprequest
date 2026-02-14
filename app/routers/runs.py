"""REST endpoints for querying execution runs."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.run import RunDetailResponse, RunResponse
from app.services import run_service

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunResponse])
async def list_runs(
    schedule_id: str | None = Query(None, description="Filter by schedule"),
    status: str | None = Query(None, description="Filter by status"),
    start_time: datetime | None = Query(None, description="Runs after this time"),
    end_time: datetime | None = Query(None, description="Runs before this time"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List runs with optional filters and pagination."""
    return await run_service.list_runs(
        session,
        schedule_id=schedule_id,
        status=status,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )


@router.get("/{run_id}", response_model=RunDetailResponse)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a single run with its full attempt history."""
    run = await run_service.get_run_with_attempts(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
