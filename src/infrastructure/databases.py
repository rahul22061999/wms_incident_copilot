"""
Single source of truth for all SQLAlchemy Base classes and session setup.

Two separate databases, two separate Base classes — this prevents table metadata
from leaking across databases during create_all() calls.

AuditBase  → audit.db     (TicketAuditEvent)
SchedulerBase → job_schedule.db (JobScheduleEvent) — engine built by AppContextBuilder
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings

_AUDIT_DB_PATH = settings.BASE_DIR / "audit.db"
_AUDIT_DB_URL = f"sqlite+aiosqlite:///{_AUDIT_DB_PATH.as_posix()}"


class AuditBase(DeclarativeBase):
    pass


class SchedulerBase(DeclarativeBase):
    pass


# Audit session factory — used by audit_repository only.
# echo is False; flip via settings.DB_ECHO if debugging.
_audit_engine = create_async_engine(_AUDIT_DB_URL, echo=False)

AuditSessionLocal = async_sessionmaker(
    _audit_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_audit_db() -> None:
    async with _audit_engine.begin() as conn:
        await conn.run_sync(AuditBase.metadata.create_all)
