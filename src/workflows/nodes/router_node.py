"""
Router node — classifies the user query and enriches it with WMS terminology.

Two output schemas are used depending on context:
- RouterState: used for normal user requests; includes schedule/cancel_schedule
  as valid task types so the router can direct a user to the scheduler path.
- SchedulerRouterState: used when the graph is invoked by a scheduled job
  (is_scheduled_run=True). Restricts task choices to parallel/sequential only,
  preventing a monitoring job from accidentally scheduling another monitoring job
  in an infinite chain.

The model fallback chain (Ollama → Google → OpenAI) prioritises the local model
for cost and latency. If Ollama is unavailable or times out, the chain falls
through silently to the next provider.
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from domain.states.router_state import RouterState, SchedulerRouterState
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.llm_clients import get_google_llm, get_ollama_llm, get_openai_fast_llm
from infrastructure.operation_cache import ROUTER_CACHE
from infrastructure.repositories.audit_repository import insert_ticket_audit_event
from workflows.prompts.generate_router_node_prompt import router_prompt

logger = logging.getLogger(__name__)

async def router_node(state: WMState) -> dict[str,str]:

    user_query = state.description

    if not user_query:
        raise ValueError("state.description is empty")

    #if job is invoking the graph then we need to route to sequential/parallel
    output_format = SchedulerRouterState if state.is_scheduled_run else RouterState

    model = (
        get_ollama_llm(cache=ROUTER_CACHE).with_structured_output(output_format)
        .with_fallbacks([
            get_google_llm(cache=ROUTER_CACHE).with_structured_output(output_format),
            get_openai_fast_llm(cache=ROUTER_CACHE).with_structured_output(output_format)
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

    await insert_ticket_audit_event(
        ticket_number=state.ticket_number,
        user_id=state.user_id,
        job_id=None,
        node_name="router_node",
        action_name="complete_sequential_agent",
        action_type="agent",
        status="success",
        action=f"Router Node {response}",
    )

    return {
        "task": response.task,
        "enriched_query": response.enriched_query,
        "schedule_interval_seconds": response.schedule_interval_seconds,
        "schedule_condition": response.schedule_condition,
    }