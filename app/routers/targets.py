"""REST endpoints for Target CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.target import TargetCreate, TargetResponse, TargetUpdate
from app.services import target_service

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(
    data: TargetCreate,
    session: AsyncSession = Depends(get_session),
):
    """Register a new HTTP target."""
    return await target_service.create_target(session, data)


@router.get("", response_model=list[TargetResponse])
async def list_targets(session: AsyncSession = Depends(get_session)):
    """List all registered targets."""
    return await target_service.list_targets(session)


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a single target by ID."""
    target = await target_service.get_target(session, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: str,
    data: TargetUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update fields on an existing target."""
    target = await target_service.get_target(session, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return await target_service.update_target(session, target, data)


@router.delete("/{target_id}", status_code=204)
async def delete_target(
    target_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a target and all its associated schedules."""
    target = await target_service.get_target(session, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    await target_service.delete_target(session, target)
