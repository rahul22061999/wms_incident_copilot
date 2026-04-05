from typing import Literal
from langchain.tools import tool
from dotenv import load_dotenv
from agents.graph.sql_subgraph import sql_graph
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState

load_dotenv()


@tool
def sql_lookup_tool(question: str, domain: Literal["inbound", "outbound", "inventory"]):
    """:arg question: SQL query to run
        :arg domain: Domain name"""

    lookup_question_on_database = sql_graph.invoke(
        SQLGraphState(
            domain=domain,
            user_question= question
        )
    )

    final_response = lookup_question_on_database.get('result').rows

    return final_response



