"""
SQL lookup worker node — executes one subtask against the WMS database.

Accepts `state: dict` (not WMState) because it is invoked via Send() from
fan_out_edge, which passes only {"query": ..., "domain": ...} rather than the
full graph state. Returning {"parallel_results": [...]} appends to the shared
list via the operator.add reducer in WMState.

The 45-second timeout covers the full sql_subgraph round-trip (schema lookup +
SQL generation + execution). Without it, a slow database or model call would
stall the entire graph indefinitely since LangGraph has no built-in node timeout.
"""

import asyncio
import logging

from workflows.tools.sql_lookup_tool import sql_lookup_tool

logger = logging.getLogger(__name__)

async def sql_lookup_node(state: dict):

    query = state["query"]
    domain = state["domain"]

    logger.info("SQL Lookup Node started | domain=%s", domain)

    try:
        result = await asyncio.wait_for(
            sql_lookup_tool.ainvoke({
                "question": query,
                "domain": domain,
            }),
            timeout=45.0,
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


