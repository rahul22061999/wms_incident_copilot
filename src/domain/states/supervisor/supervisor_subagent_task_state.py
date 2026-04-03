from typing import Literal, List
from pydantic import BaseModel, Field


class SubAgentTaskInvokeItem(BaseModel):
    ##route to which subagent
    subagent_name: Literal["inbound_agent_node", "outbound_agent_node", "inventory_agent_node"]
    ##what the subagent will be doing
    subagent_task: str = Field( description="Subagent task" )
    ## domain name to find what domain this issue belongs to
    domain_name: Literal["inbound","outbound","inventory"]



class SupervisorToSubAgentDeligationItem(BaseModel):
    ##List of subagent task messages to
    subagent_deligations: List[SubAgentTaskInvokeItem] = Field(
        description="Supervisor deligations"
    )