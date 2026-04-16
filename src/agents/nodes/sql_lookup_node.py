import logging
import asyncio
from tools.sql_lookup_tool import sql_lookup_tool


logger  = logging.getLogger(__name__)

async def sql_lookup_node(state: dict):

    query = state["query"]
    domain = state["domain"]

    logger.info(f"SQL Lookup Node: {domain}")

    try:
        result = await asyncio.wait_for(
            sql_lookup_tool.ainvoke({
                "question": query,
                "domain": domain,
            }),
            timeout=30.0,
        )
        return {
            "parallel_results": [{
                "source": "sql_lookup_node",
                "query": query,
                "status": "success",
                "result": result,
            }],
        }

    except asyncio.TimeoutError:

        logger.error("SQL Lookup Node Timeout")
        return {
            "error": "SQL Lookup Node Timeout",
        }


