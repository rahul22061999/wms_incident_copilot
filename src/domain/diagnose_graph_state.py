from typing import Literal, Any, Annotated, List
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
import operator

def merge_subagent_responses(existing: dict, new: dict) -> dict:
    merged = {**existing}
    for task_id, responses in new.items():
        merged[task_id] = merged.get(task_id, []) + responses
    return merged


class SubAgentTaskInvokeItem(BaseModel):
    agent_name: Literal["inbound_agent_node", "outbound_agent_node", "inventory_agent_node"]
    subagent_task: str = Field( description="Subagent task" )


class SupervisorDeligationItem(BaseModel):
    deligations: list[SubAgentTaskInvokeItem] = Field(
        description="Supervisor deligations"
    )

##Private payload for Send operation
class WorkerInput(BaseModel):
    task_id: str
    agent_name: Literal["inbound_agent_node", "outbound_agent_node", "inventory_agent_node"]
    task: str
    domain: Literal["inbound", "outbound", "inventory"] | None = Field(
        default=None,
        description="Inbound and outbound domain"
    )

class SubAgentResponse(BaseModel):
    task_id: str = Field(description="Task id")
    agent_name: Literal["inbound_agent_node", "outbound_agent_node", "inventory_agent_node"]
    messages: str = Field(description="Diagnostic messages")


"""Main state for all the nodes"""
class WMState(BaseModel):
    ticket_number: str = Field( description="Ticket number")
    description: str = Field( description="Description of the ticket")
    user_id: str = Field( description="User ID")
    intent: Literal["lookup", "diagnose"] | None = Field(
        default=None,
        description="Intent decided by router"
    )
    domain: Literal["inbound", "outbound", "inventory"] = Field(
        description="Inbound and outbound domain",
        default=None
    )

    ##result node
    final_responses: str = Field(default=None, description="Final response")

    ##supervisor node states
    messages: Annotated[List[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="Diagnostic messages messages"
    )

    loop_count: int = Field(
        default=0,
        description="Loop count"
    )

    subagent_log: List[SupervisorDeligationItem] = Field(
        default_factory=list,
        description="Subagent log"
    )

    active_task_id: str = Field(
        default=None,
        description="Active task id"
    )
    final_answer: str = Field(default=None, description="Final answer")
    # state
    subagent_responses: Annotated[List[SubAgentResponse], operator.add] = Field(default_factory=list)


