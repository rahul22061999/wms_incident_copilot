from typing import Literal, Any, Annotated, List
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


"""Schema output state for nodes"""
class RoutingState(BaseModel):
    ticket_number: str = Field(description="Ticket number")
    description: str = Field(description="Description of the ticket")
    user_id: str = Field(description="User ID")
    intent: Literal["lookup", "diagnose"] = Field(description="Intent classification")
    domain: Literal["inbound", "outbound", "inventory"] = Field(description="Inbound and outbound domain")

class SubAgentTaskInvokeItem(BaseModel):
    agent_name: Literal["inbound_agent", "outbound_agent", "inventory_agent"]
    subagent_task: str = Field( description="Subagent task" )


class SupervisorDeligationItem(BaseModel):
    deligations: list[SubAgentTaskInvokeItem] = Field(
        description="Supervisor deligations"
    )

##Private payload for Send operation
class WorkerInput(BaseModel):
    task_id: str
    agent_name: Literal["inbound_agent", "outbound_agent", "inventory_agent"]
    task: str

class SubAgentResponse(BaseModel):
    task_id: str = Field(description="Task id")
    agent_name: Literal["inbound_agent", "outbound_agent", "inventory_agent"]
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
    ##Lookup node state
    ##SQL lookup node specific
    skill_context: str = Field(default=None, description="Skill context")
    table_names: str = Field(default=None, description="Table names")

    ##generate sql node
    sql: str = Field(default=None, description="SQL statement")

    ##checked sql
    checked_query: str = Field(default=None, description="Checked query")

    ##sql run node
    rows: str = Field(default=None, description="Row data")

    ##result node
    final_response: str = Field(default=None, description="Final response")

    ##supervisor node states
    messages: Annotated[List[str], add_messages] = Field(
        default=None,
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

    subagent_responses: dict[str, SubAgentResponse] = Field(
        default_factory=dict,
        description="Subagent responses keyed by task_id"
    )