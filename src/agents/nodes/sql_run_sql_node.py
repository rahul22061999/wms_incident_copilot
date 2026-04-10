from langsmith import traceable
import logging
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from models.model_loader import get_groq_llm
from dotenv import load_dotenv

from utils.logging.logging_config import setup_logging
from utils.sql_tools import WmsSqlTool

load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)

@traceable(name="sql_run_sql_node")
def sql_run_sql_node(state: SQLGraphState) -> dict:
    """Run sql's on the database"""
    run_sql_query_with_columns_tool = WmsSqlTool(get_groq_llm())

    all_results = {}
    for domain,sql in state.validated_sql.items():

        if not sql:
            state.errors.append("No sql was provided")
        state.scratch["last_query"] = sql

        state.scratch["last_query"] = sql
        try:
            rows = run_sql_query_with_columns_tool.run_query(sql)
            all_results[domain] = {"rows": rows}
        except Exception as e:
            state.errors.append(str(e))
            all_results[domain] = {"rows": None, "error": str(e)}

    logger.info("SQL NODE: Sql ran on the database")
    return {
        "execution_result": all_results,
        "event_log": [{"node": "sql_run_sql_node", "message": \
            "SQL Ran successfully" if all_results else "SQL Run failed"}],
    }