from infrastructure.job_schedule_database import Base
from sqlalchemy import DateTime, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone


class JobScheduleEvent(Base):
    __tablename__ = 'job_schedule_event'

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String, nullable=False)
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
