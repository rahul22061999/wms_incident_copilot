"""
Ticket diagnosis service.

Orchestrates the diagnosis graph invocation for a single ticket. Wraps
the graph run in a semaphore to bound the number of concurrent expensive
workflows (LLM calls + multi-agent fan-out) the process will run.
"""

import logging

from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.app_context import AppContext
from workflows.graph.application_graph import graph

logger = logging.getLogger(__name__)


class TicketDiagnosisError(Exception):
    """Raised when ticket diagnosis graph execution fails."""


async def diagnose_ticket_service(
        ticket_number: str,
        session_id: str,
        user_id: str,
        description: str,
        ctx: AppContext,
):
    """
    Run the diagnosis graph for a single ticket, throttled by the
    shared graph semaphore.

    Accepts plain parameters — no dependency on API request schemas.
    The route handler is responsible for unpacking the request body.
    """
    try:
        async with ctx.graph_semaphore:
            ai_result = await graph.ainvoke(
                WMState(
                    ticket_number=ticket_number,
                    session_id=session_id,
                    user_id=user_id,
                    description=description,
                )
            )
        summarized_result = ai_result.get("summarized_result")

        if summarized_result is None:
            raise TicketDiagnosisError("Missing summarized_result in graph response")

        return summarized_result

    except TicketDiagnosisError:
        logger.exception(
            "Ticket diagnosis failed",
            extra={"ticket_number": ticket_number, "session_id": session_id, "user_id": user_id},
        )
        raise
    except Exception as exc:
        logger.exception(
            "Unexpected ticket diagnosis failure",
            extra={"ticket_number": ticket_number, "session_id": session_id, "user_id": user_id},
        )
        raise TicketDiagnosisError("Ticket diagnosis failed") from exc
