from typing import Literal
from langgraph.types import Command
from domain.sql_graph_state import SQLGraphState
from langgraph.graph import END
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

def sql_result_node(state: SQLGraphState) -> Command[Literal["__end__"]]:
    raw = state.query_rows

    if not raw:
        final = "No data found."
    else:
        if isinstance(raw, str):
            rows = eval(raw)  # safe — data from our own DB, contains datetime.date()
        else:
            rows = raw

        df = pd.DataFrame(rows)
        final = df.to_markdown(index=False)

    return Command(
        update={"final_response": final},
        goto=END,
    )