from pydantic import BaseModel, ConfigDict, Field


class DiagnosisResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    detailed_response: str = Field(
        description=(
            "The complete, fully detailed answer to the user's question. Do NOT "
            "truncate or summarize — preserve all steps, sub-steps, warnings, and "
            "context from the sub-agent findings. Format with markdown: ## headings, "
            "bullet points, numbered lists for procedures, **bold** for critical items."
        ),
    )

    citations: str = Field(
        description=(
            "Source references supporting the response, e.g. 'Inbound SOP Section 3.2', "
            "'Warehouse Handbook Ch. 4'. Empty if no sources were consulted."
        ),
    )
