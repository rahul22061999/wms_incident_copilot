import pandas as pd
import datetime
from decimal import Decimal

from domain.states.supervisor.diagnose_graph_state import WMState


def result_node(state: WMState) -> dict:
    """Single result node for both lookup and diagnose flows."""
    intent = state.get("intent")

    if intent == "lookup":
        # SQL path — format query_rows
        raw = state.get("query_rows")
        if not raw:
            final = "No data found."
        else:
            if isinstance(raw, str):
                rows = eval(
                    raw,
                    {"__builtins__": {}},
                    {"Decimal": Decimal, "datetime": datetime},
                )
            else:
                rows = raw
            df = pd.DataFrame(rows)
            final = df.to_markdown(index=False)

    elif intent == "diagnose":
        # Supervisor path — already has final answer
        final = state.get("final_responses") or "No diagnosis available."

    else:
        final = "Unknown intent."

    return {"final_responses": final}