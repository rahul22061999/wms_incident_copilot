from pydantic import BaseModel, Field


class TicketDiagnosisRequest(BaseModel):
    ticket_number: str = Field(..., min_length=1, max_length=100)
    session_id: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=4000)
