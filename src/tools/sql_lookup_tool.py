from typing import Literal
from langchain.tools import tool
from dotenv import load_dotenv
from langgraph.prebuilt import ToolRuntime

from agents.graph.sql_subgraph import sql_graph
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState

load_dotenv()


@tool(description="Lookup sql on the database")
def sql_lookup_tool(question: str, domain: Literal["inbound", "outbound", "inventory"], runtime: ToolRuntime):
    """
    Run a SQL lookup against the WMS database for a specific domain.

    Use this tool when the user needs data retrieved from the warehouse system.
    Always pass the enriched question and the correct domain.

    Args:
        question: The enriched user question to query against.
        domain: WMS domain to query — inbound, outbound, or inventory.
    """

    lookup_question_on_database = sql_graph.invoke(
        SQLGraphState(
            domain=[domain],
            user_question= question
        )
    )



    return lookup_question_on_database.get('content')



