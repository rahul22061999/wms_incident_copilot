from typing import Literal
from langgraph.types import Command
from domain.sql_graph_state import SQLGraphState
from models.model_loader import get_groq_llm

from dotenv import load_dotenv

from utils.sql_tools import WmsSqlTool

load_dotenv()

def run_sql_node(state: SQLGraphState) -> Command[Literal["return_result_node"]]:
    """Run sql's on the database"""

    run_sql_query_with_columns_tool = WmsSqlTool(get_groq_llm())

    checked_sql = state.validated_sql
    result = run_sql_query_with_columns_tool.run_query(checked_sql)

    return Command(
        update={
            "query_rows": result
        },
        goto= "sql_result_node"
    )