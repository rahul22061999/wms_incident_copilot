from typing import Literal
from langchain_community.tools import QuerySQLCheckerTool
from langgraph.types import Command
from data.state import WMState
from models.sql_tool_loader import get_sql_tools_loader


def check_sql_node(state: WMState) -> Command[Literal["run_sql_node"]]:

    sql_tools = get_sql_tools_loader()
    _query_check = next(t for t in sql_tools if isinstance(t, QuerySQLCheckerTool))

    sql_query = state.sql

    checked_query = _query_check.invoke(sql_query)

    return Command(
        update={
            "checked_query": checked_query,
        },
        goto="run_sql_node"
    )