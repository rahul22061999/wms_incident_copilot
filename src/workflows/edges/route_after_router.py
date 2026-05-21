"""
Conditional edge: router_node → one or more downstream nodes.

Returns a list of Send() objects so LangGraph can dispatch multiple branches
in parallel when the router identifies more than one task type (e.g. a query
that is both a parallel lookup and a schedule registration).

Send(node_name, state) passes the full WMState to each branch independently.
Each branch writes into its own Annotated reducer field (parallel_results,
sequential_results, etc.) so results accumulate without overwriting each other.

The fallback to sequential_node prevents a hard failure if the LLM returns an
unrecognised task label — the query still gets answered, just via the safest path.
"""

import logging

from langgraph.types import Send
from domain.states.supervisor.diagnose_graph_state import WMState

TASK_TO_NODE = {
    "parallel": "plan_parallel_subtask_node",
    "sequential": "sequential_node",
    "schedule": "scheduler_node",
    "cancel_schedule": "cancel_schedule_node",
}

logger = logging.getLogger(__name__)

def route_after_router(state: WMState) -> list[Send]:
    sends = []

    for task in state.task:
        node = TASK_TO_NODE.get(task)
        if node:
            sends.append(Send(node, state))
        else:
            logger.warning("fan_out_tasks_edge: unknown task=%r, skipping", task)

    if not sends:
        logger.warning("fan_out_tasks_edge: no valid tasks, falling back to sequential")
        sends.append(Send("sequential_node", state))

    return sends