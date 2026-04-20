import uuid
from datetime import datetime
from typing import Optional, List
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field


def _new_id() -> str:
    return str(uuid.uuid4())

def _now() -> datetime:
    return datetime.now(ZoneInfo("America/Los_Angeles"))


class MonitoringState(BaseModel):
    query: str
    interval_seconds: int

    ticket_number: str
    user_id: str
    original_session_id: str

    is_scheduled_run: bool = False
    id: str = Field(default_factory=_new_id)
    status: str = "active"
    run_count: int = 0
    created_at: datetime = Field(default_factory=_now)
    last_run_at: Optional[datetime] = None
    last_result: Optional[List[dict]] = None