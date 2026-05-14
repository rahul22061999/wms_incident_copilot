from fastapi import APIRouter, Request, Query
from fastapi.responses import StreamingResponse

from application.stream_ticket_job_service import stream_ticket_jobs_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/{ticket_number}/jobs/stream", tags=["supervisor"])
async def stream_ticket_job(
        ticket_number: str,
        request: Request,
        user_id: str = Query(..., min_length=1),
):
    event_generator = stream_ticket_jobs_service(
        ticket_number=ticket_number,
        request=request,
        user_id=user_id,
    )

    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )