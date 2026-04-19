from dataclasses import dataclass, field
from typing import  Optional, Dict, List, Any
import operator
from typing_extensions import Annotated, Literal

from domain.states.RoutingState.router_state import RouterState
from domain.states.parallel_execution_states.parallel_execution_node_state import SubTask
from domain.states.supervisor.supervisor_evidence_states import EvidenceRecord, VerificationResult


@dataclass
class WMState:

    #Main graph functions
    ticket_number: str
    session_id: str
    user_id: str
    description: str = ""

    ##Routing
    task: str = ""
    enriched_query: str = ""

    # Planner (parallel path)
    subtasks: List[SubTask] = field(default_factory=list)

    # Worker outputs — reducer merges all parallel results
    parallel_results: Annotated[List[dict], operator.add] = field(default_factory=list)

    #Sequential results
    sequential_results: Annotated[List[dict], operator.add] = field(default_factory=list)

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
    result: Optional[dict] = None
    final_response: Optional[str] = None
    structured_response: Any = None
    tool_response: Annotated[List[dict], operator.add] = field(default_factory=list)

    evidence_records: Annotated[List[EvidenceRecord], operator.add] = field(default_factory=list)
    verification_result: VerificationResult = None




