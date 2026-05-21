from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RouterState(BaseModel):
    task: List[Literal["parallel", "sequential","schedule","cancel_schedule"]] = Field(description="Route the query based on if its a parallel task, sequential or scheduler task based on user query")
    enriched_query: str = Field(
        description=(
            "The rewritten query with supply chain terminology, domain context, "
            "and any inferred intent added — without altering the original meaning."
        )
    )

    schedule_interval_seconds: Optional[int] = Field(
        default=None,
        description="For task='schedule': interval in seconds"
    )

    schedule_condition: Optional[str] = Field(
        default=None,
        description="For task='schedule': optional trigger condition in plain English.",
    )

class SchedulerRouterState(BaseModel):
    task: List[Literal["parallel", "sequential"]] = Field(description="Route the query based on if its a parallel task, sequential or scheduler task based on user query")
    enriched_query: str = Field(
        description=(
            "The rewritten query with supply chain terminology, domain context, "
            "and any inferred intent added — without altering the original meaning."
        )
    )
    schedule_interval_seconds: Optional[int] = Field(
        default=None,
        description="For task='schedule': interval in seconds"
    )

    schedule_condition: Optional[str] = Field(
        default=None,
        description="For task='schedule': optional trigger condition in plain English.",
    )