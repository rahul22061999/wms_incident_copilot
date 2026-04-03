"""Schema output state for routing node"""
from typing import Literal
from pydantic import BaseModel, Field


class RoutingState(BaseModel):
    intent: Literal["lookup", "diagnose"] = Field(
        description="lookup = direct data retrieval; diagnose = root-cause investigation"
    )
    domain: Literal["inbound", "outbound", "inventory"] = Field(
        description="Which warehouse domain the request is about"
    )