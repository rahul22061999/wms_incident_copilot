from langsmith import traceable
import logging
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from dotenv import load_dotenv
from utils.sql_tools import AsyncWMSSQLService

load_dotenv()


logger = logging.getLogger(__name__)

@traceable(name="sql_run_sql_node")
async def sql_run_sql_node(state: SQLGraphState) -> dict:
    """Run sql's on the database"""

    run_sql_query_with_columns_tool = AsyncWMSSQLService()

    all_results = {}

    for domain,sql in state.validated_sql.items():

        logger.info(
            "starting SQL execution SQL:%s",
            sql
        )
        if not sql:
            state.errors.append("No sql was provided")
            all_results[domain] = {"rows": None, "error": "No SQL was provided"}
            continue

        try:
            rows = await run_sql_query_with_columns_tool.run_query(sql)
            all_results[domain] = {"rows": rows, "error": None}
        except Exception as e:
            state.errors.append(str(e))
            all_results[domain] = {"rows": None, "error": str(e)}

        logger.info(
            "SQL execution completed"
        )

    content = {
        domain: {
            "sql": state.validated_sql.get(domain),
            "rows": all_results[domain].get("rows"),
            "error": all_results[domain].get("error"),
        }
        for domain, result in all_results.items()
    }

    success = all(r.get("error") is None for r in all_results.values())
    logger.info("SQL node completed. Success: %s, Domains: %s", success, list(all_results.keys()))

    return {
        "source": "sql",
        "content": content,
        "execution_result": all_results,
        "event_log": [{"node": "sql_run_sql_node", "message": \
            "SQL Ran successfully" if all_results else "SQL Run failed"}],
    }