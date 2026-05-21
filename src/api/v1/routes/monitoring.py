from fastapi import APIRouter, Request
from fastapi.params import Depends
from fastapi.responses import StreamingResponse

from api.v1.auth import User, get_current_user
from application.stream_job_updates import stream_ticket_jobs_service
from infrastructure.app_context import AppContext
from infrastructure.context_access import get_app_context
from infrastructure.rate_limiter import limiter

router = APIRouter(prefix="/v1/tickets", tags=["monitoring"])


@router.get("/{ticket_number}/jobs/stream", tags=["monitoring"])
@limiter.limit("10/minute")
async def stream_ticket_router(
        ticket_number: str,
        request: Request,
        current_user: User = Depends(get_current_user),
        ctx: AppContext =  Depends(get_app_context)
):
    event_generator = stream_ticket_jobs_service(
        ticket_number=ticket_number,
        request=request,
        user_id=current_user.id,
        ctx=ctx,
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