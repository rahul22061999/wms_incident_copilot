from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from temporal.schemas import MonitoringInput

with workflow.unsafe.imports_passed_through():
    from temporal.activities.monitoring_activities import run_monitoring_job


@workflow.defn
class MonitoringWorkflow:
    def __init__(self) -> None:
        self.status = "active"
        self.run_count = 0
        self.last_result = ""

    @workflow.query
    def get_status(self) -> dict:
        return {
            "status": self.status,
            "run_count": self.run_count,
            "last_result": self.last_result,
        }

    @workflow.run
    async def run(self, payload: MonitoringInput) -> dict:
        while self.run_count < payload.max_runs:
            self.status = "running"

            self.last_result = await workflow.execute_activity(
                run_monitoring_job,
                payload,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )

            self.run_count += 1
            self.status = "active"

            if self.run_count >= payload.max_runs:
                break

            await workflow.sleep(payload.interval_seconds)

        self.status = "completed"

        return {
            "job_id": payload.job_id,
            "ticket_number": payload.ticket_number,
            "run_count": self.run_count,
            "last_result": self.last_result,
            "status": self.status,
        }