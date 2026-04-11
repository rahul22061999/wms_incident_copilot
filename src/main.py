import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import ToolMessage

from agents.graph.application_graph import graph
from domain.states.supervisor.diagnose_graph_state import WMState

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnosticRequest(BaseModel):
    ticket_number: str
    session_id: str
    user_id: str
    description: str

from fastapi.responses import StreamingResponse

@app.post("/diagnose-stream")
def diagnose_stream(req: DiagnosticRequest):
    def event_generator():
        try:
            for namespace, mode, payload in graph.stream(
                    {
                        "ticket_number": req.ticket_number,
                        "session_id": req.session_id,
                        "user_id": req.user_id,
                        "description": req.description,
                    }
                    ,
                    config={"configurable": {"thread_id": req.session_id}},
                    stream_mode=["messages", "custom"],  # ← add "custom"
                    subgraphs=True,
            ):
                if mode == "custom":
                    # payload is whatever you passed to writer()
                    token = payload.get("token", "") if isinstance(payload, dict) else ""
                    if token:
                        yield f"data: {json.dumps({'token': token})}\n\n"
                    continue

                if mode != "messages":
                    continue

                message_chunk, metadata = payload
                if isinstance(message_chunk, ToolMessage):
                    continue

                raw = getattr(message_chunk, "content", "") or ""
                if isinstance(raw, list):
                    text = "".join(
                        b.get("text", "")
                        for b in raw
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                else:
                    text = raw

                if text:
                    yield f"data: {json.dumps({'token': text})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )