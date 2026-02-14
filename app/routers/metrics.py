"""REST endpoint for aggregated metrics."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.metrics import MetricsResponse
from app.services import metrics_service

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(session: AsyncSession = Depends(get_session)):
    """Return aggregated metrics across all schedules and runs."""
    return await metrics_service.get_metrics(session)
