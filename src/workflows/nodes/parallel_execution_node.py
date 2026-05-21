"""
Parallel planner node — decomposes the enriched query into independent subtasks.

This node PLANS but does not EXECUTE. It produces a list of SubTask objects
that fan_out_edge then dispatches to sql_lookup_node or sop_retrieval_node
in parallel. Keeping planning and execution separate allows the prompt to focus
purely on decomposition logic without being confused by tool availability.

The prompt enforces a default of ONE subtask — most WMS queries are not
genuinely multi-domain and over-decomposition produces worse answers by
fragmenting context. Splitting only happens when the user explicitly asks for
data from two independent sources (e.g. "check inventory AND the SOP").
"""

from langchain_core.messages import SystemMessage, HumanMessage
from domain.states.parallel_state import ParallelExecutionPlan
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.operation_cache import PARALLEL_SUBTASK_NODE_CACHE
from infrastructure.llm_clients import get_ollama_llm, get_google_llm, get_openai_fast_llm
from workflows.prompts.generate_parallel_node_prompt import parallel_node_prompt


async def plan_parallel_subtask_node(
    state: WMState,
):
    """Break the enriched query into independent subtasks for parallel execution."""

    enriched_user_query = state.enriched_query

    ##Break the query into subtasks
    llm = (
        get_ollama_llm(cache=PARALLEL_SUBTASK_NODE_CACHE).with_structured_output(ParallelExecutionPlan)
        .with_fallbacks([
            get_google_llm(cache=PARALLEL_SUBTASK_NODE_CACHE).with_structured_output(ParallelExecutionPlan),
            get_openai_fast_llm(cache=PARALLEL_SUBTASK_NODE_CACHE).with_structured_output(ParallelExecutionPlan)
        ])
    )

    plan_subagent_subtasks = await llm.ainvoke(
        [
            SystemMessage(content=parallel_node_prompt),
            HumanMessage(content=enriched_user_query),
        ])


    return {
        "subtasks": plan_subagent_subtasks.subtasks,
    }




