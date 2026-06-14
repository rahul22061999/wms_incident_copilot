"""
JobSchedulerService — registers and cancels durable monitoring schedules.

API workers do NOT own an AsyncIOScheduler, so this service never touches
APScheduler. It only writes schedule state to the DB; the dedicated scheduler
process reconciles those rows into live jobs (and removes cancelled ones).

Job IDs are a deterministic SHA-256 of (query, interval, ticket, user) so that
scheduling the same monitor twice is idempotent — create_scheduled_job returns
(job_already_scheduled, False) instead of inserting a duplicate.
"""

import hashlib

from infrastructure.app_context import AppContext
from infrastructure.repositories.job_schedule_repository import JobScheduleRepository


class JobSchedulerService:
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.repository = JobScheduleRepository(ctx.job_schedule_session_factory)

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

        return await self.repository.create_scheduled_job(
            job_id=job_id,
            query=query,
            ticket_number=ticket_number,
            session_id=session_id,
            user_id=user_id,
            interval_seconds=interval_seconds,
        )

    async def cancel_job(self, ticket_number: str) -> bool:
        # Delete the DB row only; the scheduler process removes the live
        # APScheduler job on its next reconcile cycle.
        job_id = await self.repository.get_job_id_for_ticket(ticket_number)
        if not job_id:
            return False
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
