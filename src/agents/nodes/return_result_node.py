from typing import Literal
from langgraph.types import Command
from data.state import WMState
from langgraph.graph import END


def return_result_node(state: WMState) -> Command[Literal["__end__"]]:
    final_response = f"""
        skill domain used: {state.domain}
        Result: {state.rows}
        """.strip()

    return Command(
        update={
            "final_response": final_response,
            "messages": final_response
        },
        goto=END
    )