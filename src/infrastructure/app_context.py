"""
Application-wide runtime context.

AppContext is a frozen dataclass that holds every shared resource the process
needs: DB engines, scheduler, semaphore, and the event bus. It is created once
during startup (AppContextBuilder.build) and injected wherever needed via
FastAPI's Depends(get_app_context).

frozen=True  — prevents any node or service from accidentally replacing a
               field (e.g. swapping out the scheduler mid-request).
slots=True   — reduces per-instance memory and speeds up attribute access;
               safe here because the field set is fixed at definition time.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from infrastructure.job_event_bus import JobEventBus
from utils.sql_tools import AsyncWMSSQLService

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class AppContext:
    """Immutable bag of shared runtime resources, built once and injected everywhere."""

    executor: ThreadPoolExecutor
    # Bounds concurrent LangGraph runs — each run fans out to multiple LLM calls,
    # so without a ceiling the process can exhaust API rate limits under load.
    graph_semaphore: asyncio.Semaphore

    job_schedule_engine: AsyncEngine
    job_schedule_session_factory: async_sessionmaker[AsyncSession]
    # None in API/worker processes — only the dedicated scheduler process owns a
    # live AsyncIOScheduler. API workers just write schedule state to the DB.
    scheduler: AsyncIOScheduler | None
    # In-process pub/sub: job runner publishes, SSE streams subscribe.
    # Only works within a single process — not safe across gunicorn workers.
    job_event_bus: JobEventBus

    ##wms db
    async_wms_sql_service: AsyncWMSSQLService




