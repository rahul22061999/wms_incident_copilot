from typing import Optional
from sqlalchemy import select
from domain.models.ticket_audit_event import TicketAuditEvent
from domain.schemas.ticket_audit_event_schema import (
    TicketAuditEventRead,
)
from infrastructure.audit_database_setup import AsyncSessionLocal


async def insert_ticket_audit_event(
    ticket_number: Optional[str],
    user_id: Optional[str],
    job_id: Optional[str],
    node_name: str,
    action_name: str,
    action_type: str,
    status: str,
    action: str,
    error: Optional[str] = None,
) -> TicketAuditEventRead:
    async with AsyncSessionLocal() as session:
        event = TicketAuditEvent(
            ticket_number=ticket_number,
            user_id=user_id,
            job_id=job_id,
            node_name=node_name,
            action_name=action_name,
            action_type=action_type,
            status=status,
            action=action,
            error=error,
        )

        session.add(event)
        await session.commit()
        await session.refresh(event)

        return TicketAuditEventRead.model_validate(event)



async def get_ticket_audit_events(
    ticket_number: str,
) -> list[TicketAuditEventRead]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(TicketAuditEvent)
            .where(TicketAuditEvent.ticket_number == ticket_number)
            .order_by(TicketAuditEvent.id.asc())
        )

        result = await session.execute(stmt)
        events = result.scalars().all()

        return [
            TicketAuditEventRead.model_validate(event)
            for event in events
        ]
