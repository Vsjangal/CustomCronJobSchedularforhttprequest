"""
API Scheduler — Cron-like HTTP request scheduler.

Entry point for the FastAPI application.  On startup the database tables are
created (if missing) and the background scheduler engine begins polling.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import async_session, init_db
from app.routers import metrics, runs, schedules, targets
from app.scheduler.engine import SchedulerEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger(__name__)

scheduler_engine = SchedulerEngine(session_factory=async_session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB + start scheduler.  Shutdown: stop scheduler."""
    logger.info("Initializing database tables")
    await init_db()
    await scheduler_engine.start()
    yield
    await scheduler_engine.stop()
    logger.info("Shutdown complete")


app = FastAPI(
    title="API Scheduler",
    description="Cron-like service that lets you schedule HTTP requests to external targets.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(targets.router)
app.include_router(schedules.router)
app.include_router(runs.router)
app.include_router(metrics.router)


@app.get("/health", tags=["health"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "healthy"}
