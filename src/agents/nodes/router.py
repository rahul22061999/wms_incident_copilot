from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from domain.states.RoutingState.routing_decision_state import RoutingDecision
from domain.states.supervisor.diagnose_graph_state import WMState
from models.model_loader import get_openai_fast_llm, get_google_llm
from prompts.task_prompt import ROUTER_NODE_PROMPT

@traceable(name="Routing Decision")
def router_node(state: WMState) -> dict[str, dict]:
    description = state.description
    if not description:
        raise ValueError("state.description is empty")

    model = (
        get_google_llm().with_structured_output(RoutingDecision)
        .with_fallbacks([
            get_openai_fast_llm().with_structured_output(RoutingDecision)
        ])
    )

    response = model.invoke(
        [
            SystemMessage(content=ROUTER_NODE_PROMPT),
            HumanMessage(content=description),
        ]
    )

    decision = response if isinstance(response, RoutingDecision) else RoutingDecision(**response)

    return {
        "routing_decision": decision.model_dump()
    }