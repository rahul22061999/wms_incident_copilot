# """Application service for monitoring use cases.
#
# This module coordinates Temporal + persistence for monitoring jobs.
# It should not contain Temporal workflow definitions, Temporal activities,
# SQLAlchemy query details, or FastAPI route logic.
# """
#
# import hashlib
# import logging
#
# from temporal.client import TASK_QUEUE, get_temporal_client, make_workflow_id
# from temporal.schemas import ACTIVE_STATUSES, MonitoringInput
# from temporal.workflows.monitoring_workflow import MonitoringWorkflow
# from infrastructure.monitoring_registry import (
#     create_monitor,
#     get_monitor,
#     update_monitor,
#     list_jobs_for_ticket as list_jobs_for_ticket_from_registry,
# )
#
# logger = logging.getLogger(__name__)
#
#
# def make_job_id(
#     query: str,
#     interval_seconds: int,
#     ticket_number: str,
#     user_id: str,
# ) -> str:
#     raw = f"{query.strip().lower()}::{interval_seconds}::{ticket_number}::{user_id}"
#     return str(int(hashlib.sha256(raw.encode()).hexdigest()[:12], 16))
#
#
# async def schedule_task(
#     query: str,
#     interval_seconds: int,
#     ticket_number: str,
#     session_id: str,
#     user_id: str,
# ) -> tuple[str, bool]:
#     """Create and start a durable monitoring workflow if it does not already exist.
#
#     Returns:
#         tuple[str, bool]: (job_id, created)
#     """
#     client = await get_temporal_client()
#
#     job_id = make_job_id(
#         query=query,
#         interval_seconds=interval_seconds,
#         ticket_number=ticket_number,
#         user_id=user_id,
#     )
#     workflow_id = make_workflow_id(job_id)
#
#     existing = await get_monitor(job_id)
#
#     if existing and existing.status in ACTIVE_STATUSES:
#         return job_id, False
#
#     await create_monitor(
#         job_id=job_id,
#         ticket_number=ticket_number,
#         interval_seconds=interval_seconds,
#     )
#
#     await client.start_workflow(
#         MonitoringWorkflow.run,
#         MonitoringInput(
#             job_id=job_id,
#             query=query,
#             interval_seconds=interval_seconds,
#             ticket_number=ticket_number,
#             session_id=session_id,
#             user_id=user_id,
#         ),
#         id=workflow_id,
#         task_queue=TASK_QUEUE,
#     )
#
#     return job_id, True
#
#
# async def cancel_job(job_id: str) -> None:
#     """Cancel a Temporal monitoring workflow and mark the job cancelled in storage."""
#     client = await get_temporal_client()
#     workflow_id = make_workflow_id(job_id)
#     handle = client.get_workflow_handle(workflow_id)
#
#     await handle.cancel()
#     await update_monitor(job_id, status="cancelled")
#
#
# async def get_job_status(job_id: str) -> dict:
#     """Return live Temporal workflow status for a monitoring job."""
#     client = await get_temporal_client()
#     workflow_id = make_workflow_id(job_id)
#     handle = client.get_workflow_handle(workflow_id)
#
#     return await handle.query(MonitoringWorkflow.get_status)
#
#
# async def list_jobs_for_ticket(ticket_number: str, user_id: str) -> list[dict]:
#     """List active monitoring jobs for a ticket.
#
#     Temporary wrapper around the legacy registry until repository extraction is complete.
#     """
#     return await list_jobs_for_ticket_from_registry(ticket_number, user_id)
#
#
# async def cancel_jobs_for_ticket(ticket_number: str, user_id: str) -> int:
#     """Cancel every active monitoring workflow for a ticket/user pair."""
#     jobs = await list_jobs_for_ticket(ticket_number, user_id)
#     cancelled_count = 0
#
#     for job in jobs:
#         job_id = str(job["job_id"])
#
#         try:
#             await cancel_job(job_id)
#             cancelled_count += 1
#         except Exception:
#             logger.exception(
#                 "Failed to cancel monitoring job",
#                 extra={
#                     "job_id": job_id,
#                     "ticket_number": ticket_number,
#                     "user_id": user_id,
#                 },
#             )
#
#     return cancelled_count

"""Application service for monitoring use cases.

This module coordinates Temporal + persistence for monitoring jobs.
It should not contain Temporal workflow definitions, Temporal activities,
SQLAlchemy query details, or FastAPI route logic.
"""

import hashlib
import logging

from temporal.client import TASK_QUEUE, get_temporal_client, make_workflow_id
from temporal.schemas import ACTIVE_STATUSES, MonitoringInput
from temporal.workflows.monitoring_workflow import MonitoringWorkflow
from infrastructure.monitoring_registry import (
    create_monitor,
    get_monitor,
    update_monitor,
    list_jobs_for_ticket as list_jobs_for_ticket_from_registry,
)

logger = logging.getLogger(__name__)


def make_job_id(
    query: str,
    interval_seconds: int,
    ticket_number: str,
    user_id: str,
) -> str:
    raw = f"{query.strip().lower()}::{interval_seconds}::{ticket_number}::{user_id}"
    return str(int(hashlib.sha256(raw.encode()).hexdigest()[:12], 16))


async def schedule_task(
    query: str,
    interval_seconds: int,
    ticket_number: str,
    session_id: str,
    user_id: str,
) -> tuple[str, bool]:
    """Create and start a durable monitoring workflow if it does not already exist.

    Returns:
        tuple[str, bool]: (job_id, created)
    """
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

    await client.start_workflow(
        MonitoringWorkflow.run,
        MonitoringInput(
            job_id=job_id,
            query=query,
            interval_seconds=interval_seconds,
            ticket_number=ticket_number,
            session_id=session_id,
            user_id=user_id,
        ),
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    return job_id, True


async def cancel_job(job_id: str) -> None:
    """Cancel a Temporal monitoring workflow and mark the job cancelled in storage."""
    client = await get_temporal_client()
    workflow_id = make_workflow_id(job_id)
    handle = client.get_workflow_handle(workflow_id)

    await handle.cancel()
    await update_monitor(job_id, status="cancelled")


async def get_job_status(job_id: str) -> dict | None:
    """Return the current status of a monitoring job from persisted state.

    Returns None if no job with this ID exists.
    """
    monitor = await get_monitor(job_id)

    if not monitor:
        return None

    return {
        "job_id": monitor.job_id,
        "ticket_number": monitor.ticket_number,
        "status": monitor.status,
        "run_count": monitor.run_count,
        "last_result": monitor.last_result,
        "interval_seconds": monitor.interval_seconds,
        "created_at": monitor.created_at,
        "last_run_time": monitor.last_run_time,
    }


async def list_jobs_for_ticket(ticket_number: str, user_id: str) -> list[dict]:
    """List active monitoring jobs for a ticket."""
    return await list_jobs_for_ticket_from_registry(ticket_number, user_id)


async def cancel_jobs_for_ticket(ticket_number: str, user_id: str) -> int:
    """Cancel every active monitoring workflow for a ticket/user pair."""
    jobs = await list_jobs_for_ticket(ticket_number, user_id)
    cancelled_count = 0

    for job in jobs:
        job_id = str(job["job_id"])

        try:
            await cancel_job(job_id)
            cancelled_count += 1
        except Exception:
            logger.exception(
                "Failed to cancel monitoring job",
                extra={
                    "job_id": job_id,
                    "ticket_number": ticket_number,
                    "user_id": user_id,
                },
            )

    return cancelled_count