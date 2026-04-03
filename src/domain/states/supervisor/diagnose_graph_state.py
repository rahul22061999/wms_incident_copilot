from typing import Literal, Annotated, List
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from domain.states.supervisor.supervisor_subagent_task_state import SupervisorToSubAgentDeligationItem


"""Main state for all the nodes"""
class WMState(BaseModel):
    ticket_number: str = Field( description="Ticket number")
    description: str = Field( description="Description of the ticket")
    intent: Literal["lookup", "diagnose"] | None = Field(
        default=None,
        description="Intent decided by router"
    )
    domain: Literal["inbound", "outbound", "inventory"] = Field(
        description="Inbound and outbound domain",
        default=None
    )

    ##supervisor node states
    messages: Annotated[List[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="Diagnostic messages messages"
    )

    loop_count: int = Field(
        default=0,
        description="Loop count"
    )

    subagent_task_deligation_item: List[SupervisorToSubAgentDeligationItem] = Field(
        default_factory=list,
        description="Subagent log"
    )


    final_responses: str = Field(default=None, description="Final answer")


