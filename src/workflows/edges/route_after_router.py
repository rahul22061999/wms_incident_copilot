# edges/fan_out_tasks_edge.py
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

    if getattr(state, "is_scheduled_run", False):
        sends.append(Send("plan_parallel_subtask_node", state))
        return sends

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