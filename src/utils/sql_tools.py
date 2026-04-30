from typing import Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from config import settings
import re


_READ_ONLY_START = {"select", "with", "explain"}
_BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|merge|call|copy)\b",
    re.IGNORECASE,
)

class AsyncWMSSQLService:
    _instance: Optional['AsyncWMSSQLService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncWMSSQLService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        self.engine: AsyncEngine = create_async_engine(
            url=settings.DATABASE_URL.get_secret_value(),
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "statement_timeout": str(settings.DB_STATEMENT_TIMEOUT)
                }
            },
            execution_options={"postgresql_readonly": True}
        )

    def _validate_sql(self, sql: str) -> str:
        sql = sql.strip().rstrip(";").strip()
        if not sql:
            raise ValueError("Empty SQL")

        first = sql.split(None, 1)[0].lower()
        if first not in _READ_ONLY_START:
            raise ValueError("Only read-only SELECT / WITH / EXPLAIN allowed")

        if _BLOCKED.search(sql):
            raise ValueError("Blocked non-read-only SQL detected")

        if ";" in sql:
            raise ValueError("Multiple statements are not allowed")

        return sql

    async def run_query(self, sql: str) -> list[dict[str, Any]]:
        safe_sql = self._validate_sql(sql)

        async with self.engine.connect() as conn:
            result = await conn.execute(text(safe_sql))

            if not result.returns_rows:
                return []

            rows = result.mappings().all()
            return [dict(row) for row in rows]



    async def aclose(self) -> None:
        await self.engine.dispose()


# Global instance for use in nodes
sql_service = AsyncWMSSQLService()
