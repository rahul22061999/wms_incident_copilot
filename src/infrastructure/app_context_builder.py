"""
Startup and shutdown orchestration for AppContext.

AppContextBuilder owns every resource that needs explicit cleanup (DB engines,
thread pools, scheduler). It registers teardown callbacks on an AsyncExitStack
so that shutdown always runs in reverse-construction order even if one step
raises — the stack unwinds all registered callbacks regardless.

Usage:
    ctx, stack = await AppContextBuilder(settings).build()
    # ...
    await stack.aclose()   # triggers all registered teardowns
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from concurrent.futures import ThreadPoolExecutor as PythonThreadPoolExecutor

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor as APSchedulerThreadPoolExecutor
from infrastructure.app_context import AppContext
from infrastructure.job_event_bus import JobEventBus

logger = logging.getLogger(__name__)


class AppContextBuilder:
    """
    Builds application-wide runtime context.
    Owns startup resources and registers shutdown cleanup.
    """

    def __init__(self, app_settings):
        self.settings = app_settings
        self._stack = AsyncExitStack()

    async def build(self) -> tuple[AppContext, AsyncExitStack]:
        try:
            executor = self._build_executor()

            graph_semaphore = asyncio.Semaphore(
                self.settings.MAX_GRAPH_SEMAPHORE
            )

            #Scheduling monitoring jobs using db
            job_schedule_engine, job_schedule_session_factory = await self._build_scheduler_db()
            scheduler = self._build_scheduler()
            scheduler.start()
            logger.info("Scheduler started: running=%s", scheduler.running)

            ctx = AppContext(
                executor=executor,
                graph_semaphore=graph_semaphore,
                job_schedule_engine=job_schedule_engine,
                job_schedule_session_factory=job_schedule_session_factory,
                scheduler=scheduler,
                job_event_bus=JobEventBus(),
            )

            return ctx, self._stack

        except Exception:
            logger.exception("Exception while building app context")
            await self._stack.aclose()
            raise

    def _build_executor(self) -> PythonThreadPoolExecutor:
        executor = PythonThreadPoolExecutor(
            max_workers=self.settings.EXECUTOR_MAX_WORKERS,
            thread_name_prefix="wms-incident-api",
        )

        asyncio.get_running_loop().set_default_executor(executor)

        self._stack.push_async_callback(
            self._shutdown_executor,
            executor,
        )

        return executor

    async def _build_scheduler_db(
            self,
    ) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
        engine = create_async_engine(
            self.settings.JOB_SCHEDULER_DB_URL,
            echo=False,
            pool_size=5,
            max_overflow=0,
            pool_timeout=30,
        )

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._stack.push_async_callback(engine.dispose)

        return engine, session_factory

    def _build_scheduler(self) -> AsyncIOScheduler:
        jobstore = {
            "default": SQLAlchemyJobStore(
                url=self.settings.JOB_SCHEDULER_SYNC_DB_URL
            )
        }

        scheduler = AsyncIOScheduler(
            jobstores=jobstore,
            timezone="UTC",
        )
        self._stack.push_async_callback(
            self._shutdown_scheduler,
            scheduler,
        )

        return scheduler

    @staticmethod
    async def _shutdown_executor(executor: PythonThreadPoolExecutor) -> None:
        executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    async def _shutdown_scheduler(scheduler: AsyncIOScheduler) -> None:
        if scheduler.running:
            scheduler.shutdown(wait=False)