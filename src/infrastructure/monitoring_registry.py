from __future__ import annotations

from datetime import datetime
import hashlib
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from domain.states.monitoring_state import MonitoringState
import asyncio

from infrastructure.concurrency import get_graph_semaphore

logger = logging.getLogger(__name__)

# _scheduler = BackgroundScheduler(daemon=True)
_scheduler = AsyncIOScheduler()
# _scheduler.start()
def get_scheduler() -> AsyncIOScheduler:
    """Exposed so main.py can start/shutdown it from lifespan."""
    return _scheduler
_jobs: dict[str, MonitoringState] = {}

def _key(query: str, interval: int, ticket_number: str, user_id: str) -> str:
    raw = f"{query.strip().lower()}::{interval}::{ticket_number}::{user_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _cancel_job(job_id: str) -> bool:
    monitor = _jobs[job_id]

    if not monitor:
        return False

    try:
        _scheduler.remove_job(job_id)
    except JobLookupError:
        pass

    monitor.status = "canceled"
    return True


def schedule_task(
        query: str,
        interval_seconds: int,
        ticket_number: str,
        session_id: str,
        user_id: str,
) -> tuple[str, bool]:

    job_id  = _key(query, interval_seconds, ticket_number, user_id)
    ## if there is a job scheduled then return False and do not schedule a job
    if job_id in _jobs:
        return job_id, False

    monitor = MonitoringState(
        id=job_id,
        query=query,
        interval_seconds=interval_seconds,
        ticket_number=ticket_number,
        original_session_id=session_id,
        user_id=user_id,
    )
    _jobs[job_id] = monitor

    async def run():
        from agents.graph.application_graph import graph

        monitor = _jobs.get(job_id)
        if not monitor:
            return

        monitor.status = "running"

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
                        "monitoring_job_id": monitor.id,
                    },
                    config={
                        "configurable": {
                            "thread_id": f"monitor_{ticket_number}_{user_id}_{monitor.id}"
                        }
                    },
                )

            monitor.run_count += 1
            monitor.status = "active"
            monitor.last_run_at = datetime.now()
            monitor.last_result = [result.get("summarized_result", "")]

            logger.info(
                "Monitoring job %s completed. run_count=%s",
                job_id,
                monitor.run_count,
            )

            if monitor.run_count >= 10:
                _cancel_job(job_id)

        except Exception as e:
            monitor.status = "failed"
            monitor.last_run_at = datetime.now()
            monitor.last_result = [f"Monitoring job failed: {str(e)}"]

            logger.exception("Monitoring job %s failed", job_id)


    _scheduler.add_job(run, "interval", seconds=interval_seconds, id=job_id, max_instances=1)
    logger.info("Scheduled %s every %ds: %r", job_id, interval_seconds, query)
    return job_id, True

def list_jobs() -> list[dict]:
    return [monitor.model_dump() for monitor in _jobs.values()]


def cancel_jobs_for_ticket(ticket_number: str, user_id: str) -> list[str]:
    cancelled = []

    for job_id, monitor in list(_jobs.items()):
        if (
            monitor.ticket_number == ticket_number
            and monitor.user_id == user_id
            and monitor.status in {"active", "running"}
        ):
            try:
                _scheduler.remove_job(job_id)
            except JobLookupError:
                pass

            monitor.status = "cancelled"
            cancelled.append(job_id)
            _jobs.pop(job_id)

    return cancelled

def list_jobs_for_ticket(ticket_number: str, user_id: str) -> list[MonitoringState]:
    """All active jobs belonging to this ticket+user."""
    return [
        m for m in _jobs.values()
        if m.ticket_number == ticket_number
        and m.user_id == user_id
        and m.status in {"active", "running"}
    ]


def get_run_count(job_id: str) -> int:
    """Return current run_count for a job, or 0 if it doesn't exist."""
    monitor = _jobs.get(job_id)
    return monitor.run_count if monitor else 0