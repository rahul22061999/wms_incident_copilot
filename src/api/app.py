from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.graph.application_graph import graph
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
    scheduler.start()

    try:
        yield
    finally:
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
        seen: dict[str, int] = {}

        initial = list_jobs_for_ticket(ticket_number, user_id)

        for m in initial:
            seen[m.id] = m.run_count

        yield _sse(
            {"jobs": [m.model_dump() for m in initial]},
            event="connected",
        )

        while True:
            if await request.is_disconnected():
                break

            current = {
                m.id: m
                for m in list_jobs_for_ticket(ticket_number, user_id)
            }

            for jid in list(seen):
                if jid not in current:
                    yield _sse({"job_id": jid}, event="job_cancelled")
                    seen.pop(jid)

            for jid, monitor in current.items():
                last_seen = seen.get(jid, 0)

                if monitor.run_count > last_seen:
                    yield _sse(
                        {
                            "job_id": jid,
                            "run_number": monitor.run_count,
                            "ran_at": monitor.last_run_at,
                            "result": monitor.last_result,
                        },
                        event="result",
                    )

                    seen[jid] = monitor.run_count

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