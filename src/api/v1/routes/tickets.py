"""
Ticket diagnosis route.

Exposes the /tickets/diagnose endpoint, which kicks off a LangGraph
investigation run for a given WMS ticket.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from api.v1.auth import User, get_current_user
from api.v1.schemas.requests import TicketDiagnosisRequest
from api.v1.schemas.responses import TicketDiagnosisResponse
from application.diagnose_ticket import TicketDiagnosisError, diagnose_ticket_service
from config import settings
from infrastructure.app_context import AppContext
from infrastructure.context_access import get_app_context
from infrastructure.rate_limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/tickets", tags=["tickets"])

@router.post(
    "/"
    "",
    response_model=TicketDiagnosisResponse,
    status_code=status.HTTP_200_OK,)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def diagnose_ticket(
        request: Request,
        payload: TicketDiagnosisRequest,
        ctx: AppContext = Depends(get_app_context),
        current_user: User = Depends(get_current_user),
):
    try:
        result = await diagnose_ticket_service(
            ticket_number=payload.ticket_number,
            session_id=payload.session_id,
            user_id=current_user.id,
            description=payload.description,
            ctx=ctx,
        )
    except TicketDiagnosisError as exc:
        logger.error("Diagnosis failed", extra={"ticket_number": payload.ticket_number}, exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "DIAGNOSIS_FAILED", "message": "Ticket diagnosis could not be completed."},
        ) from exc

    return TicketDiagnosisResponse(
        ticket_number=payload.ticket_number,
        session_id=payload.session_id,
        user_id=current_user.id,
        result=result,
    )
