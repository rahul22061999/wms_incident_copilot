# import aiosqlite
# from typing import Optional, Any
#
# from config import BASE_DIR
#
# DB_PATH = BASE_DIR / "audit.db"
#
#
# # Initialize the DB for the first run
# async def init_audit_db() -> None:
#     async with aiosqlite.connect(DB_PATH) as conn:
#         await conn.execute(
#             """
#             CREATE TABLE IF NOT EXISTS ticket_audit_events (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#
#                 ticket_number TEXT,
#                 user_id TEXT,
#                 job_id TEXT,
#
#                 node_name TEXT NOT NULL,
#                 action_name TEXT NOT NULL,
#                 action_type TEXT NOT NULL,
#                 status TEXT NOT NULL,
#
#                 action TEXT NOT NULL,
#                 error TEXT,
#
#                 created_at TEXT DEFAULT CURRENT_TIMESTAMP
#             );
#             """
#         )
#
#         await conn.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_ticket_audit_events_ticket_number
#             ON ticket_audit_events(ticket_number);
#             """
#         )
#
#         await conn.execute(
#             """
#             CREATE INDEX IF NOT EXISTS idx_ticket_audit_events_job_id
#             ON ticket_audit_events(job_id);
#             """
#         )
#
#         await conn.commit()
#
#
# # Common insert audit event function
# async def insert_ticket_audit_event(
#     ticket_number: str,
#     user_id: Optional[str],
#     job_id: Optional[str],
#     node_name: str,
#     action_name: str,
#     action_type: str,
#     status: str,
#     action: str,
#     error: Optional[str] = None,
# ) -> None:
#     async with aiosqlite.connect(DB_PATH) as conn:
#         await conn.execute(
#             """
#             INSERT INTO ticket_audit_events (
#                 ticket_number,
#                 user_id,
#                 job_id,
#                 node_name,
#                 action_name,
#                 action_type,
#                 status,
#                 action,
#                 error
#             )
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
#             """,
#             (
#                 ticket_number,
#                 user_id,
#                 job_id,
#                 node_name,
#                 action_name,
#                 action_type,
#                 status,
#                 action,
#                 error
#             ),
#         )
#
#         await conn.commit()
#
#
# # Read ticket audit events
# async def get_ticket_audit_events(ticket_number: str) -> list[dict[str, Any]]:
#     async with aiosqlite.connect(DB_PATH) as conn:
#         conn.row_factory = aiosqlite.Row
#
#         cursor = await conn.execute(
#             """
#             SELECT *
#             FROM ticket_audit_events
#             WHERE ticket_number = ?
#             ORDER BY id ASC;
#             """,
#             (ticket_number,),
#         )
#
#         rows = await cursor.fetchall()
#
#     return [dict(row) for row in rows]

# repositories/ticket_audit_repository.py

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.ticket_audit_event import TicketAuditEvent
from domain.schemas.ticket_audit_event_schema import (
    TicketAuditEventCreate,
    TicketAuditEventRead,
)


async def insert_ticket_audit_event(
    session: AsyncSession,
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


async def insert_ticket_audit_event_from_schema(
    session: AsyncSession,
    payload: TicketAuditEventCreate,
) -> TicketAuditEventRead:
    event = TicketAuditEvent(**payload.model_dump())

    session.add(event)
    await session.commit()
    await session.refresh(event)

    return TicketAuditEventRead.model_validate(event)


async def get_ticket_audit_events(
    session: AsyncSession,
    ticket_number: str,
) -> list[TicketAuditEventRead]:
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
