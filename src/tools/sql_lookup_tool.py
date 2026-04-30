from typing import Literal, List
from langchain.tools import tool
from workflows.graph.sql_subgraph import sql_graph
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState

@tool(description="Lookup sql on the database")
async def sql_lookup_tool(
        question: str,
        domain: List[Literal["inbound", "outbound", "inventory"]]
):
    """
    Run a SQL lookup against the WMS database for a specific domain.

    Use this tool when the user needs data retrieved from the warehouse system.
    Always pass the enriched question and the correct domain.

    Args:
        question: The enriched user question to query against.
        domain: WMS domain to query — inbound, outbound, or inventory.
    """

    lookup_question_on_database = await sql_graph.ainvoke(
        SQLGraphState(
            domain=domain,
            user_question= question
        )
    )


    return lookup_question_on_database.get('content')



