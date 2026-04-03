from langchain_core.messages import AIMessage
from langgraph.types import Command
from domain.states.supervisor.diagnose_graph_state import WMState
from utils.supervisor.supervisor_previous_context import get_previous_task_findings

def force_final_answer(
    state: WMState,
    current_loop: int,
    max_loops: int,
) -> Command:
    findings = get_previous_task_findings(state)

    return Command(
        update={
            "loop_count": current_loop + 1,
            "final_responses": f"Max loops reached. Findings: {findings}",
            "messages": [
                AIMessage(
                    content=(
                        f"[supervisor] Max investigation loops ({max_loops}) reached. "
                        f"Best-effort summary based on findings so far:\n{findings}"
                    )
                )
            ],
        },
        goto="diagnose_result_node",
    )