import logging

from tools.rag_lookup_tool import sop_retrieval_tool
import asyncio

logger = logging.getLogger(__name__)


async def sop_lookup_node(state: dict):
    query = state['query']

    logger.info(f"Sop lookup query: {query}")

    try:
        result = await asyncio.wait_for(sop_retrieval_tool.ainvoke({
            'query': query,
        }),
            timeout=5
        )

        return {
            "parallel_results": [{
                "source": "sop_retrieval_tool",
                "query": query,
                "status": "success",
                "result": result,
            }],
        }

    except asyncio.TimeoutError:

        return {
            "error": "Timeout error",
        }
