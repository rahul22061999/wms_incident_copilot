import logging

from api.schemas.ticket_schema import TicketDiagnosisRequest
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.concurrency import get_graph_semaphore
from workflows.graph.application_graph import graph

logger = logging.getLogger(__name__)


class TicketDiagnosisError(Exception):
    """Raised when ticket diagnosis graph execution fails."""


async def diagnose_ticket_service(payload: TicketDiagnosisRequest):
    try:
        ai_result = await graph.ainvoke(
                WMState(
                    ticket_number=payload.ticket_number,
                    session_id=payload.session_id,
                    user_id=payload.user_id,
                    description=payload.description,
                )
            )
        summarized_result = ai_result.get("summarized_result")

        if summarized_result is None:
            raise TicketDiagnosisError("Missing summarized_result in graph response")

        return summarized_result

    except TicketDiagnosisError:
        logger.exception(
            "Ticket diagnosis failed",
            extra={
                "ticket_number": payload.ticket_number,
                "session_id": payload.session_id,
                "user_id": payload.user_id,
            },
        )
        raise
    except Exception as exc:
        logger.exception(
            "Unexpected ticket diagnosis failure",
            extra={
                "ticket_number": payload.ticket_number,
                "session_id": payload.session_id,
                "user_id": payload.user_id,
            },
        )
        raise TicketDiagnosisError("Ticket diagnosis failed") from exc
