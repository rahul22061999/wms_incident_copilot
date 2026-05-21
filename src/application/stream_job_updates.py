"""
SSE streaming service for monitoring job updates.

Flow:
  1. Emit a "connected" event so the client knows the stream is live.
  2. Send the current DB snapshot — ensures the client is not blank if jobs
     already ran before the stream was opened.
  3. Subscribe to the JobEventBus for this ticket and block on queue.get().
     Each time MonitoringJobRunner finishes a run it calls bus.publish(), which
     wakes every waiting subscriber immediately — no polling, no DB round-trips.
  4. A 30-second wait_for timeout emits an SSE comment line (": keepalive").
     SSE comment lines are ignored by browsers but prevent nginx/proxies from
     closing the connection due to inactivity. 30 seconds is well inside the
     typical 60-second proxy idle timeout.
  5. The finally block guarantees the queue is cleaned up whether the client
     disconnects cleanly or the server shuts down mid-stream.
"""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import Request

from infrastructure.app_context import AppContext
from infrastructure.repositories.job_schedule_repository import JobScheduleRepository

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


async def stream_ticket_jobs_service(
    ticket_number: str,
    user_id: str,
    request: Request,
    ctx: AppContext,
) -> AsyncGenerator[str, None]:
    repository = JobScheduleRepository(ctx.job_schedule_session_factory)
    bus = ctx.job_event_bus

    yield _sse("connected", {"ticket_number": ticket_number, "user_id": user_id})

    # Snapshot existing jobs so the client sees current state immediately,
    # even if no new runs happen while the stream is open.
    jobs = await repository.list_run_jobs_for_ticket(ticket_number)
    for job in jobs:
        yield _sse("result", {
            "job_id": str(job["job_id"]),
            "run_count": int(job["run_count"] or 0),
            "last_run_time": job["last_run_time"],
            "last_result": job["last_result"],
            "status": job["status"],
        })

    queue = bus.subscribe(ticket_number)
    try:
        while not await request.is_disconnected():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield _sse("result", event)
            except asyncio.TimeoutError:
                # SSE comment — ignored by the browser, keeps the TCP connection alive
                yield ": keepalive\n\n"
    finally:
        bus.unsubscribe(ticket_number, queue)
