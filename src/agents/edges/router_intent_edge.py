from typing_extensions import Literal
from domain.states.supervisor.diagnose_graph_state import WMState



def router_intent_edge(state: WMState) -> Literal["lookup", "diagnose"]:
    decision = state.routing_decision
    intent = decision.intent
    if intent not in {"lookup", "diagnose"}:
        raise ValueError("routing_decision.intent is missing or invalid")
    return intent