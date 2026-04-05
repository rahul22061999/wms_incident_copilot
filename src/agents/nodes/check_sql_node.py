from langchain_community.tools import QuerySQLCheckerTool
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from models.sql_tool_loader import get_sql_tools_loader
from dotenv import load_dotenv
load_dotenv()

def check_sql_node(state: SQLGraphState) -> SQLGraphState:
    """Check and verify SQL before passing them onto database"""


    sql_check_tool: QuerySQLCheckerTool | None = None

    ##Loop over all sql tools and return only query check tool
    for tool in get_sql_tools_loader():
        if isinstance(tool, QuerySQLCheckerTool):
            sql_check_tool = tool
            break

    for domain, sql in state.generated_sql.items():
        ##check query using sql check tool
        validated_sql = sql_check_tool.invoke(sql)
        state.validated_sql[domain] = validated_sql

    return state