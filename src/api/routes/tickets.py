from fastapi import APIRouter, HTTPException
from api.schemas.ticket_schema import (
    TicketDiagnosisResponse,
    TicketDiagnosisRequest
)
from application.ticket_diagnosis_service import TicketDiagnosisError, diagnose_ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("/diagnose", response_model=TicketDiagnosisResponse)
async def diagnose_ticket(payload: TicketDiagnosisRequest):
    try:
        result = await diagnose_ticket_service(payload)
    except TicketDiagnosisError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return TicketDiagnosisResponse(
        ticket_number=payload.ticket_number,
        session_id=payload.session_id,
        user_id=payload.user_id,
        result=result,
    )
