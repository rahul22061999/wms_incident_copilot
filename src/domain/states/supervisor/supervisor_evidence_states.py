from typing import Literal, Annotated
import operator
from pydantic import BaseModel, Field


class EvidenceRecord(BaseModel):
    evidence_id: str
    source: Literal["sql", "log", "sop", "ticket"]
    content: dict = Field(default_factory=dict)

    class Config:
        extra = "ignore"



class VerificationResult(BaseModel):
    status: Literal["pass", "need_more_evidence"]

    grounded: bool

    consistent: bool
    sufficient: bool

    missing_checks: list[str] =  Field(
        description="Details of missing facts and checks from the evidence",
        default_factory= list)