from typing import Literal
from pydantic import Field, BaseModel



class RouterState(BaseModel):
    task: Literal["parallel", "sequential"] = Field(description="Route the query based on if its a parallel task or a sequential task based on user query")
    enriched_query: str = Field(
        description=(
            "The rewritten query with supply chain terminology, domain context, "
            "and any inferred intent added — without altering the original meaning."
        )
    )