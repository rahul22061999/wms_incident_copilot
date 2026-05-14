import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from fastapi import Request
from infrastructure.monitoring_registry import list_jobs_for_ticket

logger = logging.getLogger(__name__)


def _sse(data: dict, event: str) -> str:
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_ticket_jobs_service(
    ticket_number: str,
    user_id: str,
    request: Request,
) -> AsyncGenerator[str, None]:
    seen_runs_by_job_id: dict[str, int] = {}

    yield _sse(
        {
            "message": "connected",
            "ticket_number": ticket_number,
            "user_id": user_id,
        },
        event="connected",
    )

    while not await request.is_disconnected():
        try:
            jobs = await list_jobs_for_ticket(ticket_number, user_id)

            for job in jobs:
                job_id = str(job["job_id"])
                run_count = int(job.get("run_count") or 0)
                last_seen_run = seen_runs_by_job_id.get(job_id, -1)

                if run_count > last_seen_run:
                    yield _sse(
                        {
                            "job_id": job_id,
                            "run_number": run_count,
                            "ran_at": job.get("last_run_time"),
                            "result": job.get("last_result"),
                            "status": job.get("status"),
                        },
                        event="result",
                    )
                    seen_runs_by_job_id[job_id] = run_count


            await asyncio.sleep(1)

        except Exception:
            logger.exception(
                "Failed to stream ticket jobs",
                extra={"ticket_number": ticket_number, "user_id": user_id},
            )

            yield _sse(
                {
                    "message": "Failed to list monitoring jobs",
                    "ticket_number": ticket_number,
                },
                event="error",
            )

            await asyncio.sleep(3)