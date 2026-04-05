from dataclasses import dataclass, field
from typing import  Optional, Dict, List, Any



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
    ticket_number: str
    session_id: str
    description: str = ""
    loop_count: int = 0
    max_turns: int = 0
    error: Optional[str] = None
    final: bool = False
    task_description: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    routing_decision: Optional[dict] = None
    lookup_result: Optional[dict] = None
    diagnosis_result: Optional[dict] = None
    final_response: Optional[str] = None
    file_history: List[Dict[str, Any]] = field(default_factory=list)
    plugin_state: Dict[str, Any] = field(default_factory=dict)
    usage: Dict[str, Any] = field(default_factory=dict)
    budget_state: Dict[str, Any] = field(default_factory=dict)
    scratchpad_directory: Optional[str] = None
