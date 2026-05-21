"""
APScheduler job entrypoint for monitoring runs.

APScheduler calls this module-level async function by reference (stored in the
jobstore). It must be importable at the top level and cannot be a method or
closure, which is why it lives here rather than inside JobSchedulerService.

get_app_context() is called at invocation time (not at schedule time) so the
runner always gets the live AppContext even after a server restart that
re-hydrated jobs from the persistent SQLAlchemy jobstore.
"""

from infrastructure.context_access import get_app_context
from infrastructure.repositories.job_schedule_repository import JobScheduleRepository
from workers.monitoring_job_runner import MonitoringJobRunner


async def run_monitoring_job(
    query: str,
    ticket_number: str,
    session_id: str,
    user_id: str,
    job_id: str,
) -> None:
    ctx = get_app_context()

    repository = JobScheduleRepository(ctx.job_schedule_session_factory)
    runner = MonitoringJobRunner(ctx, repository)

    await runner.run(
        query=query,
        ticket_number=ticket_number,
        session_id=session_id,
        user_id=user_id,
        job_id=job_id,
    )