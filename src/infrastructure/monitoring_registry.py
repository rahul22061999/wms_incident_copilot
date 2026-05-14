from __future__ import annotations

import hashlib
import logging
from datetime import datetime

from sqlalchemy import select
from temporalio.exceptions import WorkflowAlreadyStartedError

from temporal.client import TASK_QUEUE, get_temporal_client, make_workflow_id
from temporal.schemas import MAX_RUNS, MonitoringInput

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = {"active", "running"}


async def get_monitor(job_id: str):
    """Fetch persisted monitoring job metadata by job ID."""
    from domain.models.job_schedule_event import JobScheduleEvent
    from infrastructure.job_schedule_database import AsyncLocalSession

    async with AsyncLocalSession() as session:
        return await session.get(JobScheduleEvent, job_id)


async def create_monitor(
    job_id: str,
    ticket_number: str,
    interval_seconds: int,
) -> None:
    """Persist or reset monitoring job metadata before starting the workflow."""
    from domain.models.job_schedule_event import JobScheduleEvent
    from infrastructure.job_schedule_database import AsyncLocalSession

    async with AsyncLocalSession() as session:
        existing = await session.get(JobScheduleEvent, job_id)
        now = datetime.utcnow()

        if existing:
            existing.status = "active"
            existing.last_result = ""
            existing.run_count = 0
            existing.last_run_time = now
            existing.interval_seconds = interval_seconds
            existing.ticket_number = ticket_number
            await session.commit()
            return

        session.add(
            JobScheduleEvent(
                job_id=job_id,
                ticket_number=ticket_number,
                status="active",
                event_type="temporal_workflow",
                last_result="",
                interval_seconds=interval_seconds,
                run_count=0,
                created_at=now,
                last_run_time=now,
            )
        )
        await session.commit()


async def update_monitor(
    job_id: str,
    status: str,
    last_result: str | None = None,
    increment_run_count: bool = False,
) -> None:
    """Update persisted monitoring job metadata after workflow/activity changes."""
    from domain.models.job_schedule_event import JobScheduleEvent
    from infrastructure.job_schedule_database import AsyncLocalSession

    async with AsyncLocalSession() as session:
        monitor = await session.get(JobScheduleEvent, job_id)

        if not monitor:
            logger.warning("Monitor job not found", extra={"job_id": job_id})
            return

        monitor.status = status
        monitor.last_run_time = datetime.utcnow()

        if last_result is not None:
            monitor.last_result = last_result

        if increment_run_count:
            monitor.run_count += 1

        await session.commit()


# --- DELETE MONITOR FUNCTION

async def delete_monitor(job_id: str) -> None:
    """Delete persisted monitoring job metadata by job ID."""
    from domain.models.job_schedule_event import JobScheduleEvent
    from infrastructure.job_schedule_database import AsyncLocalSession

    async with AsyncLocalSession() as session:
        monitor = await session.get(JobScheduleEvent, job_id)

        if not monitor:
            logger.warning("Monitor job not found for deletion", extra={"job_id": job_id})
            return

        await session.delete(monitor)
        await session.commit()


async def list_jobs_for_ticket(ticket_number: str, user_id: str) -> list[dict]:
    """List active persisted monitoring jobs for a ticket.

    The current JobScheduleEvent model does not appear to include user_id, so user_id
    is accepted for API compatibility but not used in the query yet.
    """
    from domain.models.job_schedule_event import JobScheduleEvent
    from infrastructure.job_schedule_database import AsyncLocalSession

    async with AsyncLocalSession() as session:
        stmt = select(JobScheduleEvent).where(
            JobScheduleEvent.ticket_number == ticket_number,
            JobScheduleEvent.status.in_(ACTIVE_STATUSES),
        )

        result = await session.execute(stmt)
        monitors = list(result.scalars().all())

        return [
            {
                "job_id": m.job_id,
                "workflow_id": make_workflow_id(str(m.job_id)),
                "ticket_number": m.ticket_number,
                "status": m.status,
                "event_type": m.event_type,
                "interval_seconds": m.interval_seconds,
                "run_count": m.run_count,
                "last_result": m.last_result,
                "created_at": m.created_at,
                "last_run_time": m.last_run_time,
            }
            for m in monitors
        ]


# --- NEW FUNCTION: list_all_jobs_for_ticket
async def list_all_jobs_for_ticket(ticket_number: str, user_id: str) -> list[dict]:
    """List all persisted monitoring jobs for a ticket, regardless of status.

    The current JobScheduleEvent model does not appear to include user_id, so user_id
    is accepted for API compatibility but not used in the query yet.
    """
    from domain.models.job_schedule_event import JobScheduleEvent
    from infrastructure.job_schedule_database import AsyncLocalSession

    async with AsyncLocalSession() as session:
        stmt = select(JobScheduleEvent).where(
            JobScheduleEvent.ticket_number == ticket_number,
        )

        result = await session.execute(stmt)
        monitors = list(result.scalars().all())

        return [
            {
                "job_id": m.job_id,
                "workflow_id": make_workflow_id(str(m.job_id)),
                "ticket_number": m.ticket_number,
                "status": m.status,
                "event_type": m.event_type,
                "interval_seconds": m.interval_seconds,
                "run_count": m.run_count,
                "last_result": m.last_result,
                "created_at": m.created_at,
                "last_run_time": m.last_run_time,
            }
            for m in monitors
        ]


def make_job_id(
    query: str,
    interval_seconds: int,
    ticket_number: str,
    user_id: str,
) -> str:
    """Create a stable monitoring job ID from the business identity of the job."""
    raw = f"{query.strip().lower()}::{interval_seconds}::{ticket_number}::{user_id}"
    return str(int(hashlib.sha256(raw.encode()).hexdigest()[:12], 16))


async def schedule_task(
    query: str,
    interval_seconds: int,
    ticket_number: str,
    session_id: str,
    user_id: str,
) -> tuple[str, bool]:
    """Start a Temporal monitoring workflow.

    Returns:
        tuple[str, bool]: (job_id, created)

    This function persists basic job metadata and starts the Temporal workflow.
    Long term, persistence should move to infrastructure/repositories/monitoring_job_repository.py.
    """
    from temporal.workflows.monitoring_workflow import MonitoringWorkflow
    client = await get_temporal_client()

    job_id = make_job_id(
        query=query,
        interval_seconds=interval_seconds,
        ticket_number=ticket_number,
        user_id=user_id,
    )
    workflow_id = make_workflow_id(job_id)

    existing = await get_monitor(job_id)

    if existing and existing.status in ACTIVE_STATUSES:
        return job_id, False

    await create_monitor(
        job_id=job_id,
        ticket_number=ticket_number,
        interval_seconds=interval_seconds,
    )

    payload = MonitoringInput(
        job_id=job_id,
        query=query,
        interval_seconds=interval_seconds,
        ticket_number=ticket_number,
        session_id=session_id,
        user_id=user_id,
        max_runs=MAX_RUNS,
    )

    try:
        await client.start_workflow(
            MonitoringWorkflow.run,
            payload,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
    except WorkflowAlreadyStartedError:
        logger.info(
            "Temporal monitoring workflow already exists",
            extra={"workflow_id": workflow_id, "job_id": job_id},
        )
        return job_id, False

    logger.info("Started Temporal monitoring workflow", extra={"workflow_id": workflow_id})
    return job_id, True


async def cancel_job(job_id: str) -> bool:
    """Cancel a Temporal monitoring workflow by job ID and remove the DB row."""
    client = await get_temporal_client()
    workflow_id = make_workflow_id(job_id)
    handle = client.get_workflow_handle(workflow_id)

    try:
        await handle.cancel()
    except Exception:
        logger.exception(
            "Failed to cancel Temporal monitoring workflow; deleting DB row anyway",
            extra={"workflow_id": workflow_id, "job_id": job_id},
        )

    await delete_monitor(job_id)

    logger.info(
        "Removed monitoring job",
        extra={"workflow_id": workflow_id, "job_id": job_id},
    )
    return True


async def get_job_status(job_id: str) -> dict:
    """Query live status from a Temporal monitoring workflow."""
    from temporal.workflows.monitoring_workflow import MonitoringWorkflow
    client = await get_temporal_client()
    workflow_id = make_workflow_id(job_id)
    handle = client.get_workflow_handle(workflow_id)

    return await handle.query(MonitoringWorkflow.get_status)


async def cancel_jobs_for_ticket(ticket_number: str, user_id: str) -> list[str]:
    """Cancel every active persisted monitoring workflow for a ticket."""
    jobs = await list_all_jobs_for_ticket(ticket_number, user_id)
    cancelled_job_ids: list[str] = []

    for job in jobs:
        job_id = str(job["job_id"])
        cancelled = await cancel_job(job_id)

        if cancelled:
            cancelled_job_ids.append(job_id)

    return cancelled_job_ids
