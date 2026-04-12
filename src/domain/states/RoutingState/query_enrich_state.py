from typing import Literal, List

from pydantic import BaseModel, Field



class QueryEnrichNode(BaseModel):
    enriched_query: str = Field(
        description=(
            "The rewritten query with supply chain terminology, domain context, "
            "and any inferred intent added — without altering the original meaning."
        )
    )

    routing_decision: List[Literal["inbound", "outbound", "inventory"]]