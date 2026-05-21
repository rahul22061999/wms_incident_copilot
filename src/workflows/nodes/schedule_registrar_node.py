import logging

from application.schedule_monitoring import JobSchedulerService
from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.context_access import get_app_context

logger = logging.getLogger(__name__)


async def schedule_registrar_node(state: WMState) -> dict:
    """Register a durable monitoring job for the current ticket."""

    logger.info(
        "Monitoring registrar entered: ticket=%s user=%s session=%s query=%r interval=%s",
        state.ticket_number,
        state.user_id,
        state.session_id,
        state.enriched_query,
        state.schedule_interval_seconds,
    )

    interval_seconds = state.schedule_interval_seconds or 30

    ctx = get_app_context()
    scheduler_service = JobSchedulerService(ctx)

    job_id, is_created = await scheduler_service.schedule_job(
        query=state.enriched_query,
        interval_seconds=interval_seconds,
        ticket_number=state.ticket_number,
        session_id=state.session_id,
        user_id=state.user_id,
    )

    result = (
        "monitor_schedule_created"
        if is_created
        else "monitor_schedule_already_exists"
    )

    return {
        "scheduler_results": [result],
        "schedular_results": [result],
        "event_log": [
            {
                "node": "schedule_registrar_node",
                "message": result,
                "metadata": {
                    "job_id": job_id,
                    "ticket_number": state.ticket_number,
                    "user_id": state.user_id,
                    "interval_seconds": interval_seconds,
                },
            }
        ],
    }