from pydantic import BaseModel, Field

class TicketDiagnosisRequest(BaseModel):
    ticket_number: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=5)
    description: str = Field(default="")


class TicketDiagnosisResponse(BaseModel):
    ticket_number: str
    session_id: str
    user_id: str
    result: object


