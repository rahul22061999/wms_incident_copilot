from decimal import Decimal
import datetime
from typing import Literal

import pandas as pd
from langgraph.types import Command
from langgraph.graph import END
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState


def sql_result_node(state: SQLGraphState) -> Command[Literal["__end__"]]:
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

        # Clean up boolean-like columns
        for col in df.columns:
            if df[col].isin([0, 1]).all():
                df[col] = df[col].map({1: "YES", 0: "NO"})

        final = df.to_markdown(index=False)

    return Command(
        update={"final_responses": final},
        goto=END,
    )