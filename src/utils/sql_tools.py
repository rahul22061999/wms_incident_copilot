import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

_READ_ONLY_START = {"select", "with", "explain"}
_BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|merge|call|copy)\b",
    re.IGNORECASE,
)

class AsyncWMSSQLService:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

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

        async with self._engine.connect() as conn:
            result = await conn.execute(text(safe_sql))

            if not result.returns_rows:
                return []

            return [dict(row) for row in result.mappings().all()]

