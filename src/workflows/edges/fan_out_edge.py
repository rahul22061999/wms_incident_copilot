"""
Conditional edge: plan_parallel_subtask_node → worker nodes.

Each subtask planned by plan_parallel_subtask_node becomes an independent
Send() to the node named by task.tool. The node name must exactly match a
registered graph node ("sql_lookup_node" or "sop_retrieval_tool").

Worker nodes receive a plain dict (not WMState) because Send() bypasses normal
state propagation and passes only the dict you provide. That is why sql_lookup_node
and sop_lookup_node accept `state: dict` instead of `state: WMState`.

Short-circuits directly to synthesizer_node when the planner returns no subtasks
to avoid a dead branch that would stall the graph.
"""

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
                "domain": task.domain,
                "is_scheduled_run": state.is_scheduled_run,
            }
        )
        for task in state.subtasks
    ]