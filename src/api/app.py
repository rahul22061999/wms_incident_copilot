from contextlib import asynccontextmanager
from cli.cli import cli
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agents.graph.application_graph import graph
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.monitoring_registry import list_jobs_for_ticket, get_scheduler
import json
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP — runs once when the server starts, AFTER the loop exists
    scheduler = get_scheduler()
    scheduler.start()
    yield
    # SHUTDOWN — runs once when the server stops
    scheduler.shutdown(wait=False)


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

    try:
        data = await graph.ainvoke(
            WMState(
                ticket_number=payload.ticket_number,
                session_id=payload.session_id,
                user_id=payload.user_id,
                description=payload.description,
            ),
            config={"configurable": {"thread_id": payload.ticket_number}}
        )

        summarized_result = data.get("summarized_result")
        if summarized_result is None:
            raise HTTPException(status_code=500, detail="Missing summarized_result in graph response")

        return summarized_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")



##Stream subscribed events to the user about the job
@app.get("/run/stream/{ticket_number}")
async def stream_for_ticket(ticket_number: str, user_id: str, request: Request):
    """Live stream of monitoring results for one user's ticket.

    Query string: ?user_id=rahul
    Sends events:
      - 'connected'     once at start, with current job list
      - 'result'        each time a tracked job completes a new run
      - 'job_cancelled' when a tracked job is removed
    """

    async def gen():
        # Per-job: highest run_count we've already pushed to the client
        seen: dict[str, int] = {}

        # Send initial state — current jobs and any results already in hand
        initial = list_jobs_for_ticket(ticket_number, user_id)
        for m in initial:
            seen[m.id] = m.run_count
        yield _sse(
            {"jobs": [m.model_dump() for m in initial]},
            event="connected",
        )

        # Stream loop
        while True:
            if await request.is_disconnected():
                break

            current = {m.id: m for m in list_jobs_for_ticket(ticket_number, user_id)}

            # Detect cancelled / completed jobs (in seen but no longer in current)
            for jid in list(seen):
                if jid not in current:
                    yield _sse({"job_id": jid}, event="job_cancelled")
                    seen.pop(jid)

            # Push new runs for currently-tracked jobs (and pick up newly-added jobs)
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


if __name__ == "__main__":
    cli()

