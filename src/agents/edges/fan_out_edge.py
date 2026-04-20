from langgraph.types import Send
from langsmith import traceable

from domain.states.supervisor.diagnose_graph_state import WMState


@traceable(name="fan_out_edge")
def fan_out_edge(state: WMState):
    """Dispatch one Send per planned subtask; short-circuit to synthesizer if none."""

    if not state.subtasks:
        return "synthesizer_node"

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