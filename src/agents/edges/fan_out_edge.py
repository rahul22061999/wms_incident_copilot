from langgraph.types import Send
from langsmith import traceable

from domain.states.supervisor.diagnose_graph_state import WMState


@traceable(name="fan_out_edge")
def fan_out_edge(state: WMState):
    """Executes action parallelly on each tool task"""
    return [
        Send(
            task.tool,
            {
                "query": task.query,
                "domain": task.domain
            }
        )
        for task in state.subtasks
    ]