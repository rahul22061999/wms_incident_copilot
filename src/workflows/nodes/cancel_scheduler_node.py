from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.monitoring_registry import cancel_jobs_for_ticket
import logging

logger = logging.getLogger(__name__)

async def cancel_scheduler_node(state: WMState) -> dict:
    cancelled_ids = await cancel_jobs_for_ticket(
        ticket_number=state.ticket_number,
        user_id=state.user_id,
    )

    logger.info(f"FOUND JOBS, CANCELLING {cancelled_ids}")

    if cancelled_ids:
        return {
            "final_response" :(
                f"Cancelled {len(cancelled_ids)} monitoring job(s) for ticket "
                f"{state.ticket_number}"
            )
        }
    return {
        "final_response": f"No active monitoring jobs found for ticket {state.ticket_number}."
    }