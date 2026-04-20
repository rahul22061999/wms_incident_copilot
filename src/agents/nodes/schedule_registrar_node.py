from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.monitoring_registry import schedule_task
import logging

logger = logging.getLogger(__name__)

def schedule_registrar_node(state: WMState) -> dict:
    """Node to register schedular jobs"""

    logger.info(
        "Registrar entered: ticket=%s user=%s session=%s query=%r interval=%s",
        state.ticket_number, state.user_id, state.session_id,
        state.enriched_query, state.schedule_interval_seconds,
    )

    job_id, is_new = schedule_task(
        query=state.enriched_query,
        interval_seconds=30,
        ticket_number=state.ticket_number,
        session_id=state.session_id,
        user_id=state.user_id,
    )

    verb = "Registered" if is_new else "Already scheduled"
    mins = (state.schedule_interval_seconds or 10) // 60

    return {
        "summarized_result": {
            "type": "schedule_created",
            "job_id": job_id,
            "interval_seconds": state.schedule_interval_seconds or 300,
            "summarized_issue": f"{verb} monitoring every {mins} min: {state.enriched_query!r}",
        }
    }