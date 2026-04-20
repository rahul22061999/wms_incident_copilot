from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    source_type: str = Field(description="sql, sop, node, or other source type")
    reference: str = Field(description="Exact citation reference")


class SynthesizerNodeReturnState(BaseModel):
    summarized_issue: str
    confidence: float
    citations: list[SourceCitation] = Field(default_factory=list)