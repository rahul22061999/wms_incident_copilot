from typing import Literal
from pydantic import BaseModel, Field


class SubAgentResponse(BaseModel):
    subagent_name: Literal["inbound_agent_node", "outbound_agent_node", "inventory_agent_node"]
    subagent_response: str = Field(description="Diagnostic messages from subagent")