import logging

from application.schedule_monitoring import JobSchedulerService
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.context_access import get_app_context

logger = logging.getLogger(__name__)

async def cancel_scheduler_node(state: WMState) -> dict:
    ctx = get_app_context()
    job_services = JobSchedulerService(ctx)

    cancelled_ids = await job_services.cancel_job(
        ticket_number=state.ticket_number,
    )

    logger.info(f"FOUND JOBS, CANCELLING {cancelled_ids}")

    if cancelled_ids:
        return {
            "final_response" :(
                f"Cancelled monitoring job(s) for ticket "
                f"{state.ticket_number}"
            )
        }
    return {
        "schedular_results": [f"monitor_schedule_canceled for ticket {state.ticket_number}"]
    }