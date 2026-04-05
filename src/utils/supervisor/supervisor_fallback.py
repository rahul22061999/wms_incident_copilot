from langchain_core.messages import AIMessage
from langgraph.types import Command
from domain.states.supervisor.diagnose_graph_state import WMState
from utils.supervisor.supervisor_previous_context import get_previous_task_findings

def force_final_answer(
    state: WMState,
    current_loop: int,
    max_loops: int,
    final_answer: str
) -> Command:

    return Command(
        update={
            "loop_count": current_loop + 1,
            "final_responses": state.final_response,
            "final": True,
            "messages": [
                {"role": "system", "content": (
                    f"[supervisor] Max investigation loops ({max_loops}) reached. "
                    f"Best-effort summary:\n{final_answer}"
                    ),
                }
            ],
        },
        goto="diagnose_result_node",
    )