from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database import Base


class TicketAuditEvent(Base):
    __tablename__ = "ticket_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ticket_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    job_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    action: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_ticket_audit_events_ticket_number", "ticket_number"),
        Index("idx_ticket_audit_events_job_id", "job_id"),
    )