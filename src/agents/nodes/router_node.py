import logging
from langchain_core.messages import SystemMessage, HumanMessage
from domain.states.RoutingState.router_state import RouterState
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.operation_cache import ROUTER_CACHE
from models.model_loader import get_ollama_llm, get_google_llm, get_openai_fast_llm
from prompts.generate_router_node_prompt import router_prompt

logger = logging.getLogger(__name__)

async def router_node(state: WMState) -> dict[str,str]:

    user_query = state.description

    if not user_query:
        raise ValueError("state.description is empty")

    model = (
        get_ollama_llm(cache=ROUTER_CACHE).with_structured_output(RouterState)
        .with_fallbacks([
            get_google_llm(cache=ROUTER_CACHE).with_structured_output(RouterState),
            get_openai_fast_llm(cache=ROUTER_CACHE).with_structured_output(RouterState)
        ])
    )

    response = await model.ainvoke(
        [
            SystemMessage(content=router_prompt),
            HumanMessage(content=user_query),
        ]
    )

    logger.info(
        "task=%r enriched=%r interval=%s condition=%r",
        response.task, response.enriched_query,
        response.schedule_interval_seconds, response.schedule_condition,
    )

    return {
        "task": response.task,
        "enriched_query": response.enriched_query,
        "schedule_interval_seconds": response.schedule_interval_seconds,
        "schedule_condition": response.schedule_condition,
    }