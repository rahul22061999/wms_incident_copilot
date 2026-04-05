from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from models.model_loader import get_groq_llm
from dotenv import load_dotenv
from utils.sql_tools import WmsSqlTool

load_dotenv()

def sql_run_sql_node(state: SQLGraphState) -> SQLGraphState:
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

    state.execution_result=all_results
    return state