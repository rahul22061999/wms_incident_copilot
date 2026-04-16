# agents/edges/route_after_router.py
import logging
from typing import Literal

from domain.states.supervisor.diagnose_graph_state import WMState

logger = logging.getLogger(__name__)


def route_after_router(state: WMState) -> Literal["parallel", "sequential"]:
    """
    Conditional edge: route to either the parallel planner or the sequential agent
    based on the router node's classification.

    Expects state.task to be set by router_node to either "parallel" or "sequential".
    Falls back to "sequential" if the task is missing or unrecognized — sequential
    is the safer default because a ReAct loop can handle parallel-ish queries
    (just slower), while fan-out cannot handle dependencies.
    """
    task = (state.task or "").strip().lower()

    if task == "parallel":
        logger.info(
            "Routing to PARALLEL path (ticket=%s, query=%s)",
            state.ticket_number,
            state.enriched_query,
        )
        return "parallel"

    if task == "sequential":
        logger.info(
            "Routing to SEQUENTIAL path (ticket=%s, query=%s)",
            state.ticket_number,
            state.enriched_query,
        )
        return "sequential"

    # Unknown or empty — fall back to the safer path
    logger.warning(
        "route_after_router: unknown task=%r, defaulting to SEQUENTIAL (ticket=%s)",
        state.task,
        state.ticket_number,
    )
    return "sequential"