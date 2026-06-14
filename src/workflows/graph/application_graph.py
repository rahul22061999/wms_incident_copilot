"""
WMS Copilot application graph.

Topology:
    START → router_node
              ↓  (route_after_router — one Send() per task type)
    ┌─────────┬──────────┬────────────┬──────────────────┐
    ▼         ▼          ▼            ▼
  parallel  sequential  scheduler  cancel_schedule
  planner    agent       node          node
    ↓         │          │             │
 fan_out_edge │          │             │
    ↓         │          │             │
sql/sop nodes │          │             │
    └─────────┴──────────┴─────────────┘
                          ↓
                   synthesizer_node → END

The compiled graph is built once at module import and reused for every request.
sql_lookup_node and sop_retrieval_node run in parallel via Send(); LangGraph
waits for all branches before advancing synthesizer_node because parallel_results
uses an operator.add reducer — the barrier is implicit in the reduce semantics.
"""

from langgraph.graph import END, START, StateGraph

from domain.states.supervisor.diagnose_graph_state import WMState
from workflows.edges.fan_out_edge import fan_out_edge
from workflows.edges.route_after_router import route_after_router
from workflows.nodes.cancel_scheduler_node import cancel_scheduler_node
from workflows.nodes.parallel_execution_node import plan_parallel_subtask_node
from workflows.nodes.router_node import router_node
from workflows.nodes.schedule_registrar_node import schedule_registrar_node
from workflows.nodes.sequential_agent import sequential_agent
from workflows.nodes.sop_lookup_node import sop_lookup_node
from workflows.nodes.sql_lookup_node import sql_lookup_node
from workflows.nodes.synthesizer_node import synthesizer_node


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
        ["plan_parallel_subtask_node", "sequential_node", "scheduler_node", "cancel_schedule_node"],
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



graph = _application_graph().compile()