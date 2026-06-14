"""
Dedicated scheduler process — the ONLY process that owns an AsyncIOScheduler.

Run exactly one instance (never scale this):

    PYTHONPATH=src uv run python -m scheduler_main

API workers never own a scheduler; they only write schedule rows to the
job_schedule_event table. This process reconciles those rows into live
APScheduler interval jobs:

  * row present in the DB but not yet registered  -> add_job()
  * job registered but whose DB row is gone       -> remove_job()  (cancellations)

Running a single scheduler process means each monitoring job fires exactly once
per tick, regardless of how many API workers are running.
"""

from __future__ import annotations

import asyncio
import logging
import signal

from apscheduler.jobstores.base import JobLookupError

from config import settings
from infrastructure.app_context_builder import AppContextBuilder
from infrastructure.context_access import get_app_context, set_app_context
from infrastructure.databases import SchedulerBase
from infrastructure.orm.job_schedule_event import JobScheduleEvent  # noqa: F401  registers table on SchedulerBase
from infrastructure.repositories.job_schedule_repository import JobScheduleRepository
from utils.logging_config import setup_logging
from workers.monitoring_job_entrypoint import run_monitoring_job

setup_logging()
logger = logging.getLogger(__name__)

RECONCILE_INTERVAL_SECONDS = 30


async def reconcile_jobs() -> None:
    """Bring the live scheduler in sync with the active schedules in the DB."""
    ctx = get_app_context()
    scheduler = ctx.scheduler
    if scheduler is None:
        return

    repository = JobScheduleRepository(ctx.job_schedule_session_factory)
    active_rows = await repository.list_active_jobs()
    active_by_id = {row["job_id"]: row for row in active_rows}

    registered_ids = {job.id for job in scheduler.get_jobs()}

    # Register schedules written by API workers that aren't live yet.
    for job_id, row in active_by_id.items():
        if job_id not in registered_ids:
            scheduler.add_job(
                func=run_monitoring_job,
                trigger="interval",
                seconds=row["interval_seconds"],
                id=job_id,
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                kwargs={
                    "query": row["query"],
                    "ticket_number": row["ticket_number"],
                    "session_id": row["session_id"],
                    "user_id": row["user_id"],
                    "job_id": job_id,
                },
            )
            logger.info("Registered monitoring job %s", job_id)

    # Remove jobs whose DB row was deleted/deactivated (cancellations).
    for job_id in registered_ids - active_by_id.keys():
        try:
            scheduler.remove_job(job_id)
            logger.info("Removed cancelled monitoring job %s", job_id)
        except JobLookupError:
            pass


async def _reconcile_loop(stop: asyncio.Future) -> None:
    """Reconcile on startup and every RECONCILE_INTERVAL_SECONDS until stopped."""
    while not stop.done():
        try:
            await reconcile_jobs()
        except Exception:
            logger.exception("Reconcile cycle failed")
        try:
            # Sleep, but wake immediately if shutdown is requested.
            await asyncio.wait_for(asyncio.shield(stop), timeout=RECONCILE_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            continue


async def main() -> None:
    builder = AppContextBuilder(settings)
    ctx, stack = await builder.build(start_scheduler=True)
    set_app_context(ctx)

    # Dev convenience — create the schedule table if missing. Use Alembic in prod.
    async with ctx.job_schedule_engine.begin() as conn:
        await conn.run_sync(SchedulerBase.metadata.create_all)

    loop = asyncio.get_running_loop()
    stop: asyncio.Future = loop.create_future()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: stop.done() or stop.set_result(None))

    reconcile_task = asyncio.create_task(_reconcile_loop(stop))

    logger.info(
        "Scheduler process running — reconciling every %ss", RECONCILE_INTERVAL_SECONDS
    )
    await stop

    logger.info("Scheduler process shutting down")
    reconcile_task.cancel()
    try:
        await reconcile_task
    except asyncio.CancelledError:
        pass
    await stack.aclose()


if __name__ == "__main__":
    asyncio.run(main())
