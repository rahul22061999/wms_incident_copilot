# domain/schemas/ticket_audit_event_schema.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TicketAuditEventCreate(BaseModel):
    ticket_number: Optional[str] = None
    user_id: Optional[str] = None
    job_id: Optional[str] = None

    node_name: str
    action_name: str
    action_type: str
    status: str

    action: str
    error: Optional[str] = None


class TicketAuditEventRead(BaseModel):
    id: int

    ticket_number: Optional[str] = None
    user_id: Optional[str] = None
    job_id: Optional[str] = None

    node_name: str
    action_name: str
    action_type: str
    status: str

    action: str
    error: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }