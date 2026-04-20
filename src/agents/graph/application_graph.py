from functools import lru_cache
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from domain.states.supervisor.diagnose_graph_state import WMState
from agents.nodes.router_node import router_node
from agents.nodes.parallel_execution_node import plan_parallel_subtask_node
from agents.nodes.sql_lookup_node import sql_lookup_node
from agents.nodes.sop_lookup_node import sop_lookup_node
from agents.nodes.synthesizer_node import synthesizer_node
from agents.edges.fan_out_edge import fan_out_edge
from agents.edges.route_after_router import route_after_router
from agents.nodes.sequential_agent import sequential_agent
from agents.nodes.schedule_registrar_node import schedule_registrar_node
from agents.nodes.cancel_scheduler_node import cancel_scheduler_node

@lru_cache(maxsize=1)
def _application_graph():
    builder = StateGraph(WMState)

    # Nodes
    builder.add_node("router_node", router_node)
    builder.add_node("plan_parallel_subtask_node", plan_parallel_subtask_node)
    builder.add_node("sql_lookup_node", sql_lookup_node)
    builder.add_node("sop_retrieval_node", sop_lookup_node)
    builder.add_node("synthesizer_node", synthesizer_node)
    builder.add_node("sequential_node", sequential_agent)
    builder.add_node("scheduler_node", schedule_registrar_node)
    builder.add_node("cancel_schedule_node", cancel_scheduler_node)

    # Entry point
    builder.add_edge(START, "router_node")

    # Router decides: parallel (for now only path) — sequential path to be added later
    builder.add_conditional_edges(
        "router_node",
        route_after_router,
        {
            "parallel": "plan_parallel_subtask_node",
            "sequential": "sequential_node",
            "schedule": "scheduler_node",
            "cancel_schedule": "cancel_schedule_node",
            # "sequential": "react_agent_node",  # add when sequential path is built
        },
    )

    # Planner -> fan-out to workers (parallel execution)
    builder.add_conditional_edges(
        "plan_parallel_subtask_node",
        fan_out_edge,
        ["sql_lookup_node", "sop_retrieval_node"],
    )

    # Workers -> synthesizer (barrier: waits for ALL parallel workers)
    builder.add_edge("sql_lookup_node", "synthesizer_node")
    builder.add_edge("sop_retrieval_node", "synthesizer_node")
    builder.add_edge("sequential_node", "synthesizer_node")
    builder.add_edge("scheduler_node", "synthesizer_node")
    builder.add_edge("cancel_schedule_node", "synthesizer_node")

    # Synthesizer → END
    builder.add_edge("synthesizer_node", END)

    return builder


_application_graph.cache_clear()
checkpointer = InMemorySaver()
graph = _application_graph().compile(checkpointer=checkpointer)
