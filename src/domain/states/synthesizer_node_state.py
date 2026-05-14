from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SourceType = Literal["sql", "sop", "node", "job", "other"]


class SourceCitation(BaseModel):

    source_type: SourceType = Field(
        description="Origin of the cited evidence."
    )
    reference: str = Field(
        min_length=1,
        description="Exact citation reference (e.g. table.column, SOP ID, node name, job_id).",
    )


class SynthesizerNodeReturnState(BaseModel):

    summarized_issue: str = Field(
        min_length=1,
        description="One- or two-sentence summary of the diagnosed issue.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the diagnosis, between 0 and 1.",
    )
    citations: list[SourceCitation] = Field(
        default_factory=list,
        description="Evidence supporting the summarized issue.",
    )