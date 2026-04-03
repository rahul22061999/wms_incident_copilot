from typing import Literal
from langchain_community.tools import QuerySQLCheckerTool
from langgraph.types import Command
from domain.sql_graph_state import SQLGraphState
from models.sql_tool_loader import get_sql_tools_loader
from dotenv import load_dotenv
load_dotenv()

def check_sql_node(state: SQLGraphState) -> Command[Literal["run_sql_node"]]:
    """Check and verify SQL before passing them onto database"""

    sql_check_tool: QuerySQLCheckerTool | None = None

    ##Loop over all sql tools and return only query check tool
    for tool in get_sql_tools_loader():
        if isinstance(tool, QuerySQLCheckerTool):
            sql_check_tool = tool
            break

    sql_query = (state.generated_sql or "").strip()

    ##check query using sql check tool
    validated_sql = sql_check_tool.invoke(sql_query)

    return Command(
        update={
            "validated_sql": validated_sql,
        },
        goto="run_sql_node"
    )