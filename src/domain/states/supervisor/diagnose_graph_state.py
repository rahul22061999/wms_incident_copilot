from dataclasses import dataclass, field
from langchain_core.messages import AnyMessage
from domain.states.RoutingState.routing_decision_state import RoutingDecision
from domain.states.sql_subgraph_state.sql_lookup_result import LookupResult
from domain.states.supervisor.diagnosis_result import DiagnosisResult


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
    description: str | None = None
    messages: list[AnyMessage] = field(default_factory=list)
    user_context: dict[str, str] = field(default_factory=dict)
    system_context: dict[str, str] = field(default_factory=dict)
    routing_decision: RoutingDecision | None = None
    lookup_result: LookupResult | None = None
    diagnosis_result: DiagnosisResult | None = None
    # final_response: str | None = None
    # usage: UsageStats = field(default_factory=UsageStats)
    # budget_state: BudgetState = field(default_factory=BudgetState)
    # event_log: list[Event] = field(default_factory=list)