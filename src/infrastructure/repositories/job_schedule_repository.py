"""
Repository for JobScheduleEvent persistence.

Each method opens and closes its own session via `async with session_factory()`.
This is intentional: SQLite has limited concurrent writer support, and holding
a session open across async yield points (like the SSE stream loop) would
serialize all DB access for the lifetime of the connection. Short-lived sessions
minimise lock contention.

expire_on_commit=False on the session factory means ORM objects returned from
a committed session stay usable without triggering a lazy-load SELECT — safe
here because every method returns immediately after commit.
"""

from datetime import datetime, timezone

from sqlalchemy import delete, select, update

from infrastructure.orm.job_schedule_event import JobScheduleEvent


class JobScheduleRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create_scheduled_job(
        self,
        job_id: str,
        query: str,
        ticket_number: str,
        session_id: str,
        user_id: str,
        interval_seconds: int,
        is_active: bool = True,
    ) -> tuple[str, bool]:
        async with self.session_factory() as session:
            existing_stmt = select(JobScheduleEvent.job_id).where(
                JobScheduleEvent.job_id == job_id
            )
            existing = await session.execute(existing_stmt)

            if existing.scalar_one_or_none() is not None:
                return "job_already_scheduled", False

            event = JobScheduleEvent(
                job_id=job_id,
                query=query,
                ticket_number=ticket_number,
                session_id=session_id,
                user_id=user_id,
                status="active",
                event_type="monitoring_scheduled",
                last_result="",
                interval_seconds=interval_seconds,
                run_count=0,
                is_active=is_active,
                created_at=datetime.now(timezone.utc),
            )

            session.add(event)

            await session.commit()

            return str(datetime.now(timezone.utc)), True


    async def get_run_count(self, job_id: str) -> int:
        async with self.session_factory() as session:
            stmt = (
                select(JobScheduleEvent.run_count)
                .where(JobScheduleEvent.job_id == job_id)
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none() or 0

    async def get_job_id_for_ticket(self, ticket_number: str) -> str:
        async with self.session_factory() as session:
            stmt = (
                select(JobScheduleEvent.job_id)
                .where(JobScheduleEvent.ticket_number == ticket_number)
            )

            result = await session.execute(stmt)

            return result.scalar_one_or_none() or None

    async def mark_running(self, job_id: str) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(JobScheduleEvent)
                .where(JobScheduleEvent.job_id == job_id)
                .values(
                    status="running",
                    event_type="monitoring_running",
                    run_count=JobScheduleEvent.run_count + 1,
                    last_run_time=datetime.now(timezone.utc),
                )
            )

            await session.execute(stmt)
            await session.commit()

    async def mark_completed(self, job_id: str, result: str) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(JobScheduleEvent)
                .where(JobScheduleEvent.job_id == job_id)
                .values(
                    status="active",
                    event_type="monitoring_completed",
                    last_result=result,
                )
            )

            await session.execute(stmt)
            await session.commit()

    async def mark_failed(self, job_id: str, error: str) -> None:
        async with self.session_factory() as session:
            stmt = (
                update(JobScheduleEvent)
                .where(JobScheduleEvent.job_id == job_id)
                .values(
                    status="failed",
                    event_type="monitoring_failed",
                    last_result=error,
                )
            )

            await session.execute(stmt)
            await session.commit()

    async def delete_job(self, job_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = delete(JobScheduleEvent).where(JobScheduleEvent.job_id == job_id)

            result = await session.execute(stmt)
            await session.commit()

            return getattr(result, "rowcount", 0) > 0

    async def list_run_jobs_for_ticket(self, ticket_number: str) -> list[dict]:
        async with self.session_factory() as session:

            stmt = (
                select(
                    JobScheduleEvent.job_id,
                    JobScheduleEvent.run_count,
                    JobScheduleEvent.last_run_time,
                    JobScheduleEvent.last_result,
                    JobScheduleEvent.status
                )
                .where(JobScheduleEvent.ticket_number == ticket_number)
            )

            result = await session.execute(stmt)

            return list(result.mappings().all())

    async def list_active_jobs(self) -> list[dict]:
        """All active schedules, with everything needed to register an APScheduler job.

        Read by the dedicated scheduler process on startup and on each
        reconciliation tick to register any schedules the API workers have
        written to the DB but that aren't yet live in the scheduler.
        """
        async with self.session_factory() as session:
            stmt = select(
                JobScheduleEvent.job_id,
                JobScheduleEvent.query,
                JobScheduleEvent.ticket_number,
                JobScheduleEvent.session_id,
                JobScheduleEvent.user_id,
                JobScheduleEvent.interval_seconds,
            ).where(JobScheduleEvent.is_active.is_(True))

            result = await session.execute(stmt)

            return list(result.mappings().all())