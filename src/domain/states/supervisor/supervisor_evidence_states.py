from typing import Literal, Annotated
import operator
from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    evidence_id: str
    source: Literal["sql", "log", "sop", "ticket"]
    content: Annotated[dict, operator.or_] = Field(default_factory=dict)



class VerificationResult(BaseModel):
    status: Literal["pass", "need_more_evidence", "human_review", "reject"]

    grounded: bool
    consistent: bool
    sufficient: bool

    missing_checks: list[str] = []
    risk_flags: list[str] = []