from typing import Literal, List
from pydantic import BaseModel, Field



class RoutingDecision(BaseModel):
    intent: Literal["lookup", "diagnose"] = Field(
        description="lookup = direct data retrieval; diagnose = root-cause investigation"
    )
    domain: List[Literal["inbound", "outbound", "inventory"]] = Field(
        description="Which warehouse domain the request is about"
    )