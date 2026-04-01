from typing import Literal
from langchain_community.tools import QuerySQLDatabaseTool
from langgraph.types import Command
from data.state import WMState
from models.sql_tool_loader import get_sql_tools_loader



def run_sql_node(state: WMState) -> Command[Literal["return_result_node"]]:
    tools = get_sql_tools_loader()
    _run_sql = next(t for t in tools if isinstance(t, QuerySQLDatabaseTool))

    checked_sql = state.checked_query
    result = _run_sql.invoke({"query": checked_sql})

    return Command(
        update={
            "rows": result
        },
        goto= "return_result_node"
    )