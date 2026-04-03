from typing import Literal
from langgraph.types import Command
from langgraph.graph import END
from domain.states.supervisor.diagnose_graph_state import WMState


def diagnose_result_node(state: WMState) -> Command[Literal["__end__"]]:
    return Command(
        update={"final_responses": state.final_responses or "No results available."},
        goto=END,
    )