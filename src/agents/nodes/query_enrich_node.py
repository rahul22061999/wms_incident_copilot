from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from domain.states.RoutingState.query_enrich_state import QueryEnrichNode
from domain.states.supervisor.diagnose_graph_state import WMState
from models.model_loader import get_openai_fast_llm, get_google_llm
from prompts.task_prompt import ENRICH_QUERY_PROMPT

@traceable(name="Routing Decision")
def query_enrich_node(state: WMState) -> dict:
    description = state.description
    if not description:
        raise ValueError("state.description is empty")

    model = (
        get_google_llm().with_structured_output(QueryEnrichNode)
        .with_fallbacks([
            get_openai_fast_llm().with_structured_output(QueryEnrichNode)
        ])
    )

    response = model.invoke(
        [
            SystemMessage(content=ENRICH_QUERY_PROMPT),
            HumanMessage(content=description),
        ]
    )


    return {
        "description": response.enriched_query,
        "routing_decision": response.routing_decision,
    }