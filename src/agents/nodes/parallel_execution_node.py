from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable
from domain.states.parallel_execution_states.parallel_execution_node_state import ParallelExecutionPlan
from domain.states.supervisor.diagnose_graph_state import WMState
from models.model_loader import get_ollama_llm, get_google_llm, get_openai_fast_llm
from prompts.generate_parallel_node_prompt import parallel_node_prompt


@traceable(name="parallel_task_plan_node")
def plan_parallel_subtask_node(
    state: WMState,
):
    """Break the enriched query into independent subtasks for parallel execution."""

    enriched_user_query = state.enriched_query

    ##Break the query into subtasks
    llm = (
        get_ollama_llm().with_structured_output(ParallelExecutionPlan)
        .with_fallbacks([
            get_google_llm().with_structured_output(ParallelExecutionPlan),
            get_openai_fast_llm().with_structured_output(ParallelExecutionPlan)
        ])
    )

    plan_subagent_subtasks = llm.invoke(
        [
            SystemMessage(content=parallel_node_prompt),
            HumanMessage(content=enriched_user_query),
        ])


    return {
        "subtasks": plan_subagent_subtasks.subtasks,
    }




