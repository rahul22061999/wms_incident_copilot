import asyncio
import logging

from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from config import settings
from temporal.activities.monitoring_activities import run_monitoring_job, cleanup_monitoring_job
from temporal.client import TASK_QUEUE, get_temporal_client
from temporal.workflows.monitoring_workflow import MonitoringWorkflow


logger = logging.getLogger(__name__)


async def run_worker() -> None:

    logger.info("Initialized graph semaphore for Temporal worker", extra={"max_graph_semaphore": settings.MAX_GRAPH_SEMAPHORE})

    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[MonitoringWorkflow],
        activities=[run_monitoring_job, cleanup_monitoring_job],
        workflow_runner=UnsandboxedWorkflowRunner(),
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())