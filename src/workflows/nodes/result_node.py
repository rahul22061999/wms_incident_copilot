
from domain.states.supervisor.diagnose_graph_state import WMState


def result_node(state: WMState):
    final_text = state.result or ""

    return {
        "final_response": final_text,
        "final": True,
    }