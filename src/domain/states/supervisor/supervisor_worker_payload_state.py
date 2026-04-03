from typing import Literal
from pydantic import BaseModel


class SupervisorWorkerPayloadState(BaseModel):

    domain_name: Literal["inbound", "outbound", "inventory"]
    worker_task: str
    subagent_name: Literal["inbound_agent_node", "outbound_agent_node", "inventory_agent_node"]
    loop_counter: int
