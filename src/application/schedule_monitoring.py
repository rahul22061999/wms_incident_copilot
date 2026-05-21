"""
JobSchedulerService — creates and cancels APScheduler interval jobs.

Job IDs are derived deterministically from (query, interval, ticket, user) via
SHA-256 so that scheduling the same monitoring request twice is idempotent:
the scheduler's replace_existing=True replaces the old trigger rather than
creating a duplicate, and the repository's create_scheduled_job returns
(job_already_scheduled, False) without inserting a second row.

cancel_job removes the APScheduler trigger first (stops future runs) then
deletes the DB record. The JobLookupError guard handles the case where the
scheduler has already pruned the job (e.g. after a restart) but the DB row
still exists.
"""

import hashlib

from apscheduler.jobstores.base import JobLookupError

from infrastructure.app_context import AppContext
from infrastructure.repositories.job_schedule_repository import JobScheduleRepository
from workers.monitoring_job_entrypoint import run_monitoring_job
from workers.monitoring_job_runner import MonitoringJobRunner


class JobSchedulerService:
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.repository = JobScheduleRepository(ctx.job_schedule_session_factory)
        self.runner = MonitoringJobRunner(ctx, self.repository)

    async def schedule_job(
        self,
        query: str,
        interval_seconds: int,
        session_id: str,
        ticket_number: str,
        user_id: str,
    ) -> tuple[str, bool]:
        job_id = self._make_job_id(
            query=query,
            interval_seconds=interval_seconds,
            ticket_number=ticket_number,
            user_id=user_id,
        )

        self.ctx.scheduler.add_job(
            func=run_monitoring_job,
            trigger="interval",
            seconds=interval_seconds,
            id=job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            kwargs={
                "query": query,
                "ticket_number": ticket_number,
                "session_id": session_id,
                "user_id": user_id,
                "job_id": job_id,
            },
        )

        job_status, is_created = await self.repository.create_scheduled_job(
            job_id=job_id,
            ticket_number=ticket_number,
            interval_seconds=interval_seconds,
        )

        return job_status, is_created

    async def cancel_job(self, ticket_number: str) -> bool:

        job_id: str = await self.repository.get_job_id_for_ticket(ticket_number)

        try:
            self.ctx.scheduler.remove_job(job_id)
        except JobLookupError:
            pass

        return await self.repository.delete_job(job_id)

    @staticmethod
    def _make_job_id(
        query: str,
        interval_seconds: int,
        ticket_number: str,
        user_id: str,
    ) -> str:
        raw = f"{query.strip().lower()}::{interval_seconds}::{ticket_number}::{user_id}"
        return str(int(hashlib.sha256(raw.encode()).hexdigest()[:12], 16))