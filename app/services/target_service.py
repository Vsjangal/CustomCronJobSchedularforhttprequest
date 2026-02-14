"""CRUD operations for Target entities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.target import Target
from app.schemas.target import TargetCreate, TargetUpdate


async def create_target(session: AsyncSession, data: TargetCreate) -> Target:
    """Persist a new Target and return it."""
    target = Target(
        name=data.name,
        url=data.url,
        method=data.method,
        headers=data.headers or {},
        body_template=data.body_template,
    )
    session.add(target)
    await session.commit()
    await session.refresh(target)
    return target


async def list_targets(session: AsyncSession) -> list[Target]:
    """Return all targets ordered by most recently created."""
    stmt = select(Target).order_by(Target.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_target(session: AsyncSession, target_id: str) -> Target | None:
    """Fetch a single target by ID, or None if not found."""
    return await session.get(Target, target_id)


async def update_target(
    session: AsyncSession, target: Target, data: TargetUpdate
) -> Target:
    """Apply partial updates to an existing Target."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    await session.commit()
    await session.refresh(target)
    return target


async def delete_target(session: AsyncSession, target: Target) -> None:
    """Remove a target and cascade-delete its schedules."""
    await session.delete(target)
    await session.commit()
