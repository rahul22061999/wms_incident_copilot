"""
Executes a single monitoring job run against the application graph.

Called by APScheduler on the configured interval via monitoring_job_entrypoint.
Each invocation:
  1. Checks the run count and self-terminates after MAX_RUNS to prevent jobs
     from running forever when no one is watching them.
  2. Acquires graph_semaphore before invoking the LangGraph pipeline so the
     scheduler cannot overload the process with concurrent LLM calls when
     multiple tickets have overlapping intervals.
  3. Publishes the result to the JobEventBus so any connected SSE streams
     receive the update immediately without polling the database.

The repository is instantiated per-run (not shared) to avoid holding a
SQLite connection open across the scheduler's thread boundary.
"""

import logging

from domain.states.supervisor.diagnose_graph_state import WMState
from infrastructure.app_context import AppContext
from infrastructure.repositories.job_schedule_repository import JobScheduleRepository

logger = logging.getLogger(__name__)


class MonitoringJobRunner:
    MAX_RUNS = 10

    def __init__(self, ctx: AppContext, repository: JobScheduleRepository):
        self.ctx = ctx
        self.repository = repository

    async def run(
        self,
        query: str,
        ticket_number: str,
        session_id: str,
        user_id: str,
        job_id: str,
    ) -> None:
        from workflows.graph.application_graph import graph

        current_run_count = await self.repository.get_run_count(job_id)

        if current_run_count >= self.MAX_RUNS:
            await self.repository.delete_job(job_id)
            self.ctx.scheduler.remove_job(job_id)
            return

        await self.repository.mark_running(job_id)

        try:
            async with self.ctx.graph_semaphore:
                ai_result = await graph.ainvoke(
                    WMState(
                        ticket_number=ticket_number,
                        session_id=session_id,
                        user_id=user_id,
                        description=query,
                        is_scheduled_run=True
                    )
                )
            result_str = str(ai_result)
            await self.repository.mark_completed(job_id, result_str)
            self.ctx.job_event_bus.publish(ticket_number, {
                "job_id": job_id,
                "run_count": current_run_count + 1,
                "status": "active",
                "last_result": result_str,
            })

            logger.info(
                "Monitoring job completed",
                extra={
                    "job_id": job_id,
                    "ticket_number": ticket_number,
                    "session_id": session_id,
                    "user_id": user_id,
                    "run_count": current_run_count,
                    "result": ai_result,
                },
            )

        except Exception as exc:
            error_str = str(exc)
            await self.repository.mark_failed(job_id, error_str)
            self.ctx.job_event_bus.publish(ticket_number, {
                "job_id": job_id,
                "run_count": current_run_count + 1,
                "status": "failed",
                "last_result": error_str,
            })
            logger.exception("Monitoring job failed", extra={"job_id": job_id})
            raise