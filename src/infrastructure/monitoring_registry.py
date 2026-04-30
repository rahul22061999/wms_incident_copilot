from __future__ import annotations

from datetime import datetime
import hashlib
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import select

from config import settings
from domain.models.job_schedule_event import JobScheduleEvent
from infrastructure.concurrency import get_graph_semaphore
from infrastructure.job_schedule_database import AsyncLocalSession

logger = logging.getLogger(__name__)


_scheduler = AsyncIOScheduler(
    jobstores={
        "default": SQLAlchemyJobStore(url=settings.JOB_SCHEDULER_DB_URL),
    }
)


def get_scheduler() -> AsyncIOScheduler:
    return _scheduler


def make_job_id(
    query: str,
    interval_seconds: int,
    ticket_number: str,
    user_id: str,
) -> int:
    raw = f"{query.strip().lower()}::{interval_seconds}::{ticket_number}::{user_id}"
    return int(hashlib.sha256(raw.encode()).hexdigest()[:12], 16)


async def get_monitor(job_id: int) -> JobScheduleEvent | None:
    async with AsyncLocalSession() as session:
        return await session.get(JobScheduleEvent, job_id)


async def create_monitor(
    job_id: int,
    ticket_number: str,
    interval_seconds: int,
) -> None:
    async with AsyncLocalSession() as session:
        existing = await session.get(JobScheduleEvent, job_id)

        if existing:
            return

        monitor = JobScheduleEvent(
            job_id=job_id,
            ticket_number=ticket_number,
            status="active",
            event_type="scheduler_job",
            last_result="",
            interval_seconds=interval_seconds,
            run_count=0,
            created_at=datetime.now(),
            last_run_time=datetime.now(),
        )

        session.add(monitor)
        await session.commit()


async def update_monitor(
    job_id: int,
    status: str,
    last_result: str | None = None,
    increment_run_count: bool = False,
) -> None:
    async with AsyncLocalSession() as session:
        monitor = await session.get(JobScheduleEvent, job_id)

        if not monitor:
            logger.warning("Monitor %s not found", job_id)
            return

        monitor.status = status
        monitor.last_run_time = datetime.now()

        if last_result is not None:
            monitor.last_result = last_result

        if increment_run_count:
            monitor.run_count += 1

        await session.commit()


async def cancel_job(job_id: int) -> bool:
    async with AsyncLocalSession() as session:
        monitor = await session.get(JobScheduleEvent, job_id)

        if not monitor:
            logger.warning("Monitor %s not found in DB", job_id)

            try:
                _scheduler.remove_job(str(job_id))
                return True
            except JobLookupError:
                return False

        try:
            _scheduler.remove_job(str(job_id))
            logger.info("Removed APScheduler job %s", job_id)
        except JobLookupError:
            logger.warning("APScheduler job %s not found, deleting DB row anyway", job_id)

        await session.delete(monitor)
        await session.commit()

        return True

async def run_monitoring_job(
    job_id: int,
    query: str,
    ticket_number: str,
    session_id: str,
    user_id: str,
) -> None:
    from workflows.graph.application_graph import graph

    monitor = await get_monitor(job_id)

    if not monitor:
        logger.warning("Job %s exists in scheduler but not DB", job_id)
        return

    if monitor.status not in {"active", "running"}:
        logger.info("Skipping job %s because status=%s", job_id, monitor.status)
        return

    await update_monitor(
        job_id=job_id,
        status="running",
        last_result=monitor.last_result,
    )

    try:
        sem = get_graph_semaphore()

        async with sem:
            result = await graph.ainvoke(
                {
                    "description": query,
                    "is_scheduled_run": True,
                    "ticket_number": ticket_number,
                    "session_id": session_id,
                    "user_id": user_id,
                    "monitoring_job_id": str(job_id),
                },
                config={
                    "configurable": {
                        "thread_id": f"monitor_{ticket_number}_{user_id}_{job_id}"
                    }
                },
            )

        summarized_result = str(result.get("summarized_result", ""))

        await update_monitor(
            job_id=job_id,
            status="active",
            last_result=summarized_result,
            increment_run_count=True,
        )

        updated_monitor = await get_monitor(job_id)

        if updated_monitor and updated_monitor.run_count >= 10:
            await cancel_job(job_id)

    except Exception as exc:
        error_message = f"Monitoring job failed: {str(exc)}"

        await update_monitor(
            job_id=job_id,
            status="failed",
            last_result=error_message,
        )

        logger.exception("Monitoring job %s failed", job_id)


async def schedule_task(
    query: str,
    interval_seconds: int,
    ticket_number: str,
    session_id: str,
    user_id: str,
) -> tuple[int, bool]:
    job_id = make_job_id(
        query=query,
        interval_seconds=interval_seconds,
        ticket_number=ticket_number,
        user_id=user_id,
    )

    existing_monitor = await get_monitor(job_id)

    if existing_monitor and existing_monitor.status in {"active", "running"}:
        return job_id, False

    await create_monitor(
        job_id=job_id,
        ticket_number=ticket_number,
        interval_seconds=interval_seconds,
    )

    if _scheduler.get_job(str(job_id)):
        return job_id, False

    _scheduler.add_job(
        run_monitoring_job,
        trigger="interval",
        seconds=interval_seconds,
        id=str(job_id),
        args=[
            job_id,
            query,
            interval_seconds,
            ticket_number,
            session_id,
            user_id,
        ],
        max_instances=1,
        replace_existing=True,
    )

    logger.info("Scheduled job %s every %s seconds", job_id, interval_seconds)

    return job_id, True


async def cancel_jobs_for_ticket(ticket_number: str, user_id: str) -> list[int]:
    cancelled: list[int] = []

    async with AsyncLocalSession() as session:
        result = await session.execute(
            select(JobScheduleEvent).where(
                JobScheduleEvent.ticket_number == ticket_number
            )
        )

        monitors = result.scalars().all()

        for monitor in monitors:
            job_id = monitor.job_id

            try:
                _scheduler.remove_job(str(job_id))
                logger.info("Removed APScheduler job %s", job_id)
            except JobLookupError:
                logger.warning("APScheduler job %s not found, deleting DB row anyway", job_id)

            cancelled.append(job_id)
            await session.delete(monitor)

        await session.commit()

    return cancelled
async def list_jobs_for_ticket(ticket_number: str, user_id: str) -> list[dict]:
    async with AsyncLocalSession() as session:
        result = await session.execute(
            select(JobScheduleEvent).where(
                JobScheduleEvent.ticket_number == ticket_number,
                JobScheduleEvent.status.in_(["active", "running"]),
            )
        )

        monitors = result.scalars().all()

        return [
            {
                "job_id": monitor.job_id,
                "ticket_number": monitor.ticket_number,
                "status": monitor.status,
                "event_type": monitor.event_type,
                "interval_seconds": monitor.interval_seconds,
                "run_count": monitor.run_count,
                "last_result": monitor.last_result,
                "created_at": monitor.created_at,
                "last_run_time": monitor.last_run_time,
            }
            for monitor in monitors
        ]