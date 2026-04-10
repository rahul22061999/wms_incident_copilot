from langchain_community.tools import QuerySQLCheckerTool
from langsmith import traceable
import logging
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from models.sql_tool_loader import get_sql_tools_loader
from dotenv import load_dotenv

from utils.logging.logging_config import setup_logging

load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)


@traceable(name="check_sql_node")
def check_sql_node(state: SQLGraphState) -> dict:
    """Check and verify SQL before passing them onto database"""


    sql_check_tool: QuerySQLCheckerTool | None = None

    ##Loop over all sql tools and return only query check tool
    for tool in get_sql_tools_loader():
        if isinstance(tool, QuerySQLCheckerTool):
            sql_check_tool = tool
            break

    validated = {}
    for domain, sql in state.generated_sql.items():
        ##check query using sql check tool
        validated_sql = sql_check_tool.invoke(sql)
        validated[domain] = validated_sql

    logger.debug("CHECK SQL NODE: Sql validated")

    return {
        "validated_sql": validated,
        "event_log": [{"node": "check_sql_node", "message": "Completed checking sql"}],
    }