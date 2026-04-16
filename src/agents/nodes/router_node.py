import logging

from langchain_core.messages import SystemMessage, HumanMessage
from domain.states.RoutingState.router_state import RouterState
from domain.states.supervisor.diagnose_graph_state import WMState
from models.model_loader import get_ollama_llm, get_google_llm, get_openai_fast_llm
from prompts.generate_router_node_prompt import router_prompt

logger = logging.getLogger(__name__)

def router_node(state: WMState) -> dict[str,str]:

    user_query = state.description

    if not user_query:
        raise ValueError("state.description is empty")

    model = (
        get_ollama_llm().with_structured_output(RouterState)
        .with_fallbacks([
            get_google_llm().with_structured_output(RouterState),
            get_openai_fast_llm().with_structured_output(RouterState)
        ])
    )

    response = model.invoke(
        [
            SystemMessage(content=router_prompt),
            HumanMessage(content=user_query),
        ]
    )
    logger.info(response)
    return {
       "task": response.task,
        "enriched_query": response.enriched_query,
    }