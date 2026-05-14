from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, TypeAlias
import operator
from typing_extensions import Annotated, Literal
from domain.states.parallel_execution_states.parallel_execution_node_state import SubTask
from domain.states.supervisor.supervisor_evidence_states import EvidenceRecord
from domain.states.synthesizer_node_state import SynthesizerNodeReturnState



GraphResult: TypeAlias = dict[str, Any]
GraphEvent: TypeAlias = dict[str, Any]
GraphError: TypeAlias = dict[str, Any]


@dataclass
class WMState:

    # input
    ticket_number: str
    session_id: str
    user_id: str
    description: str = ""


    selected_tasks: List[str] = field(default_factory=list)
    # Backwards-compatible alias for older nodes. Prefer selected_tasks in new code.
    task: List[str] = field(default_factory=list)
    enriched_query: str = ""

    # Planner (parallel path)
    subtasks: List[SubTask] = field(default_factory=list)

    # Worker outputs — reducer merges all parallel results
    parallel_results: Annotated[List[GraphResult], operator.add] = field(default_factory=list)

    #Sequential results
    sequential_results: Annotated[List[GraphResult], operator.add] = field(default_factory=list)

    # Scheduler results
    scheduler_results: Annotated[List[str], operator.add] = field(default_factory=list)
    # Backwards-compatible typo alias for older nodes. Prefer scheduler_results in new code.
    schedular_results: Annotated[List[str], operator.add] = field(default_factory=list)

    # rollback / audit trail
    status: Literal["new", "running", "failed", "done"] = "new"
    event_log: Annotated[List[GraphEvent], operator.add] = field(default_factory=list)
    errors: Annotated[List[GraphError], operator.add] = field(default_factory=list)
    current_node: str = "start"

    ##scheduler
    schedule_interval_seconds: Optional[int] = None


    loop_count: int = 0
    max_turns: int = 8
    final: bool = False
    task_description: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    result: Optional[GraphResult] = None
    final_response: Optional[str] = None
    structured_response: Optional[GraphResult] = None
    tool_response: Annotated[List[GraphResult], operator.add] = field(default_factory=list)

    evidence_records: Annotated[List[EvidenceRecord], operator.add] = field(default_factory=list)
    summarized_result: Optional[SynthesizerNodeReturnState] = None






