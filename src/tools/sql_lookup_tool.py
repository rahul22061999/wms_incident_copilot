from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.cache.memory import InMemoryCache
from dotenv import load_dotenv

from data.state import WMState
from src.agents.nodes.load_skills_node import load_skills_node
from src.agents.nodes.generate_sql_node import generate_sql_node
from src.agents.nodes.check_sql_node import check_sql_node
from src.agents.nodes.run_sql_node import run_sql_node
from src.agents.nodes.return_result_node import return_result_node

load_dotenv()


def build_sql_graph():
    builder = StateGraph(WMState)

    builder.add_node("load_skills_node", load_skills_node)
    builder.add_node("generate_sql_node", generate_sql_node)
    builder.add_node("check_sql_node", check_sql_node)
    builder.add_node("run_sql_node", run_sql_node)
    builder.add_node("return_result_node", return_result_node)

    builder.add_edge(START, "load_skills_node")
    builder.add_edge("load_skills_node", "generate_sql_node")
    builder.add_edge("generate_sql_node", "check_sql_node")
    builder.add_edge("check_sql_node", "run_sql_node")
    builder.add_edge("run_sql_node", "return_result_node")
    builder.add_edge("return_result_node", END)

    return builder.compile(cache=InMemoryCache())


sql_graph = build_sql_graph()


@tool
def sql_lookup_tool(question: str) -> str:
    """Look up SQL results for inbound questions."""
    subgraph_input = {
        "domain": "inbound",
        "description": question,
    }

    result = sql_graph.invoke(
        WMState(
            ticket_number="INC12345",
            description=question,
            user_id="rahul",
            domain="inbound"
        )
    )

    # If graph output is a dict / TypedDict-style state
    return result["final_response"]