from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.databases import SchedulerBase


class JobScheduleEvent(SchedulerBase):
    __tablename__ = 'job_schedule_event'

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String, nullable=False)
    # Full context needed to re-register the APScheduler job from this row.
    # The dedicated scheduler process reconciles jobs using these columns.
    query: Mapped[str] = mapped_column(String, nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String)
    last_result: Mapped[str] = mapped_column(String, nullable=False)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    run_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda _: datetime.now(timezone.utc),
        nullable=False,
    )
    last_run_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda _: datetime.now(timezone.utc),
        nullable=False,
    )




    __table_args__ = (
        Index("idx_job_schedule_event_job_id", "job_id"),
    )
