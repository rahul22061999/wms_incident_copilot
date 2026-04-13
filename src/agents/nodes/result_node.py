from langgraph.config import get_stream_writer
from domain.states.supervisor.diagnose_graph_state import WMState

def result_node(state: WMState):
    writer = get_stream_writer()

    final_text = state.result or ""

    return {
        "final_response": final_text,
        "final": True,
    }