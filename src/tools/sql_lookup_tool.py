from typing import Literal
from langchain.tools import tool
from dotenv import load_dotenv
from langgraph.prebuilt import ToolRuntime

from agents.graph.sql_subgraph import sql_graph
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState

load_dotenv()


@tool
def sql_lookup_tool(question: str, domain: Literal["inbound", "outbound", "inventory"], runtime: ToolRuntime):
    """

    :param question:
    :param domain:
    :param runtime:
    :return:

    The tool requires a domain, question
    """

    lookup_question_on_database = sql_graph.invoke(
        SQLGraphState(
            domain=[domain or runtime.domain],
            user_question= question
        )
    )

    final_response = lookup_question_on_database['execution_result']

    return final_response



