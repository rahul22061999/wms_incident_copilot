from functools import lru_cache
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from domain.states.supervisor.diagnose_graph_state import WMState
from agents.nodes.router import router_node
from agents.edges.router_intent_edge import router_intent_edge
from agents.nodes.supervisor_node import WarehouseSupervisorNode
from agents.nodes.result_node import result_node
from agents.nodes.sql_lookup_subgraph_node import sql_query_subgraph_node


supervisor_node = WarehouseSupervisorNode()
@lru_cache(maxsize=1)
def _application_graph():
    builder = StateGraph(WMState)

    builder.add_node("router_node", router_node)
    builder.add_node("sql_query_subgraph_node", sql_query_subgraph_node)
    builder.add_node("supervisor_node", supervisor_node)
    builder.add_node("result_node", result_node)

    builder.add_edge(START, "router_node")

    builder.add_conditional_edges(
        "router_node",
        router_intent_edge,
        {
            "lookup": "sql_query_subgraph_node",
            "diagnose": "supervisor_node",
        },
    )

    builder.add_edge("sql_query_subgraph_node", "result_node")
    builder.add_edge("supervisor_node", "result_node")
    builder.add_edge("result_node", END)

    return builder


graph = _application_graph().compile()