from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from watchfiles import awatch

from workflows.graph.application_graph import graph
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.concurrency import init_graph_semaphore, get_graph_semaphore
from infrastructure.monitoring_registry import list_jobs_for_ticket, get_scheduler


logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=64)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    loop.set_default_executor(executor)

    init_graph_semaphore(settings.MAX_GRAPH_SEMAPHORE)

    scheduler = get_scheduler()

    if not scheduler.running:
        scheduler.start()

    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)

        executor.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)


class RunRequest(BaseModel):
    ticket_number: str
    session_id: str
    user_id: str
    description: str


def _sse(data: dict, event: str) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/run")
async def run_app(payload: RunRequest):
    sem = get_graph_semaphore()

    try:
        async with sem:
            data = await graph.ainvoke(
                WMState(
                    ticket_number=payload.ticket_number,
                    session_id=payload.session_id,
                    user_id=payload.user_id,
                    description=payload.description,
                ),
                config={
                    "configurable": {
                        "thread_id": f"{payload.ticket_number}_{payload.session_id}_{payload.user_id}"
                    }
                },
            )

        summarized_result = data.get("summarized_result")

        if summarized_result is None:
            raise HTTPException(
                status_code=500,
                detail="Missing summarized_result in graph response",
            )

        return {"result": summarized_result}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Graph execution failed")
        raise HTTPException(
            status_code=500,
            detail="Graph execution failed",
        )


@app.get("/run/stream/{ticket_number}")
async def stream_for_ticket(ticket_number: str, user_id: str, request: Request):
    async def gen():
        seen: dict[int, int] = {}

        initial = await list_jobs_for_ticket(ticket_number, user_id)

        for job in initial:
            seen[job["job_id"]] = job["run_count"]

        yield _sse(
            {"jobs": initial},
            event="connected",
        )

        while True:
            if await request.is_disconnected():
                break

            jobs = await list_jobs_for_ticket(ticket_number, user_id)

            # stop polling if there are no active/running jobs left
            if not jobs:
                yield _sse(
                    {"message": "No active scheduled jobs. Closing stream."},
                    event="closed",
                )
                break

            current = {
                job["job_id"]: job
                for job in jobs
            }

            for job_id in list(seen):
                if job_id not in current:
                    yield _sse(
                        {"job_id": job_id},
                        event="job_cancelled",
                    )
                    seen.pop(job_id)

            for job_id, job in current.items():
                last_seen = seen.get(job_id, 0)

                if job["run_count"] > last_seen:
                    yield _sse(
                        {
                            "job_id": job_id,
                            "run_number": job["run_count"],
                            "ran_at": job["last_run_time"],
                            "result": job["last_result"],
                            "status": job["status"],
                        },
                        event="result",
                    )

                    seen[job_id] = job["run_count"]

            await asyncio.sleep(1)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )