from temporalio.client import Client

TEMPORAL_ADDRESS = "localhost:7233"
TASK_QUEUE = "wms-monitoring-task-queue"
MONITOR_WORKFLOW_ID_PREFIX = "monitor"


async def get_temporal_client() -> Client:
    return await Client.connect(TEMPORAL_ADDRESS)


def make_workflow_id(job_id: str) -> str:
    return f"{MONITOR_WORKFLOW_ID_PREFIX}-{job_id}"