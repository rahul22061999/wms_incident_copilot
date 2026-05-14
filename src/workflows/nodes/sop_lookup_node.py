import logging

from tools.rag_lookup_tool import sop_retrieval_tool


logger = logging.getLogger(__name__)


async def sop_lookup_node(state: dict):
    query = state['query']

    logger.info(f"Sop lookup query: {query}")

    try:
        result = await sop_retrieval_tool.ainvoke({
            'query': query,
        })


        return {
            "parallel_results": [{
                "source": "sop_retrieval_tool",
                "query": query,
                "status": "success",
                "result": result,
            }],
        }

    except Exception as e:

        logger.error(f"Exception occurred while looking up sop: {e}")

        return {
            "error": "Timeout error",
        }
