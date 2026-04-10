from dataclasses import dataclass, field
from typing import  Optional, Dict, List, Any
import operator
from typing_extensions import Annotated, Literal


# class WMState(TypedDict, total=False):
#     remaining_steps: int
#     ticket_number: str
#     description: str
#     intent: Literal["lookup", "diagnose"] | None
#     domain: Literal["inbound", "outbound", "inventory"] | None
#     messages: Annotated[list[AnyMessage], add_messages]
#     loop_count: int
#     active_agent: str | None
#     task_description: str | None
#     final_responses: str | None

@dataclass
class WMState:

    #Main graph functions
    ticket_number: str
    session_id: str
    user_id: str
    description: str = ""

    # rollback / audit trail
    status: Literal["new", "running", "failed", "done"] = "new"
    event_log: Annotated[list[dict[str, Any]], operator.add] = field(default_factory=list)
    errors: Annotated[list[dict[str, Any]], operator.add] = field(default_factory=list)
    current_node: str = "start"

    loop_count: int = 0
    max_turns: int = 0
    final: bool = False
    task_description: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    routing_decision: Optional[dict] = None
    lookup_result: Optional[dict] = None
    diagnosis_result: Optional[dict] = None
    final_response: Optional[str] = None




