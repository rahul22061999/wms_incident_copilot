from functools import lru_cache

from langgraph.graph import StateGraph, START, END
from domain.states.supervisor.diagnose_graph_state import WMState
from langgraph.checkpoint.memory import InMemorySaver
from src.agents.nodes.router import router_node
from agents.edges.router_intent_edge import router_intent_edge
from agents.nodes.supervisor_node import WarehouseSupervisorNode
from agents.nodes.result_node import result_node
from agents.nodes.sql_lookup_subgraph_node import sql_query_subgraph_node
from utils.logging.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _application_graph() -> StateGraph:
    builder = StateGraph(WMState)
    supervisor_node = WarehouseSupervisorNode()

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

    logger.info("Application graph built")

    return builder

##Persist on local memory
checkpointer = InMemorySaver()
graph = _application_graph().compile(checkpointer=checkpointer)

