import logging

from temporalio import activity

from infrastructure.concurrency import get_graph_semaphore
from temporal.schemas import ACTIVE_STATUSES, MonitoringInput

logger = logging.getLogger(__name__)


@activity.defn
async def run_monitoring_job(payload: MonitoringInput) -> str:
    from infrastructure.monitoring_registry import get_monitor, update_monitor
    from workflows.graph.application_graph import graph

    monitor = await get_monitor(payload.job_id)

    if not monitor:
        logger.warning("Job %s exists in Temporal but not DB", payload.job_id)
        return ""

    if monitor.status not in ACTIVE_STATUSES:
        logger.info(
            "Skipping job %s because status=%s",
            payload.job_id,
            monitor.status,
        )
        return ""

    await update_monitor(payload.job_id, status="running")

    try:

        result = await graph.ainvoke(
                {
                    "description": payload.query,
                    "is_scheduled_run": True,
                    "ticket_number": payload.ticket_number,
                    "session_id": payload.session_id,
                    "user_id": payload.user_id,
                    "monitoring_job_id": str(payload.job_id),
                },
                config={
                    "configurable": {
                        "thread_id": (
                            f"monitor_{payload.ticket_number}_"
                            f"{payload.user_id}_{payload.job_id}"
                        )
                    }
                },
            )

        summarized_result = str(result.get("summarized_result", ""))

        await update_monitor(
            payload.job_id,
            status="active",
            last_result=summarized_result,
            increment_run_count=True,
        )

        return summarized_result

    except Exception as exc:
        logger.exception("Monitoring job %s failed", payload.job_id)

        await update_monitor(
            payload.job_id,
            status="failed",
            last_result=f"Monitoring job failed: {exc}",
        )

        raise


@activity.defn
async def cleanup_monitoring_job(job_id: str) -> None:
    from infrastructure.monitoring_registry import delete_monitor

    await delete_monitor(job_id)