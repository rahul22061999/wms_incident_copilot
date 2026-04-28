from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from config import settings
import re


# class WmsSqlTool:
#     def __init__(self, query_check_llm: BaseChatModel):
#         self.llm = query_check_llm
#         self.db = self._create_database()
#         self.toolkit = self._create_tools()
#         self.engine: AsyncEngine = self._create_engine_with_pooling()
#
#     def _create_engine_with_pooling(self):
#         return create_async_engine(
#             url=settings.DATABASE_URL.get_secret_value(),
#             pool_size=settings.DB_POOL_SIZE,
#             max_overflow=settings.DB_MAX_OVERFLOW,
#             pool_timeout=settings.DB_POOL_TIMEOUT,
#             pool_recycle=settings.DB_POOL_RECYCLE,
#             pool_pre_ping=True,
#             connect_args={
#                 "options": f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT}"
#             },
#             execution_options={"postgresql_readonly": True}
#         )
#
#     def _create_database(self) -> SQLDatabase:
#         return SQLDatabase(
#             engine = self.engine,
#             include_tables = settings.SQL_TABLES,
#             sample_rows_in_table_info=3,
#             schema=settings.DB_SCHEMA,
#         )
#
#     # def run_query(self, sql: str) -> str:
#     #     """Run SQL with column names included."""
#     #     raw_string =  self.db.run(sql, include_columns=True)
#     #
#     #     try:
#     #         return ast.literal_eval(raw_string)
#     #     except (ValueError, SyntaxError):
#     #         return ast.literal_eval(raw_string)
#
#     async def run_query(self, sql: str) -> str:
#         """Run SQL with column names included."""
#         async with self.engine.connect() as conn:
#             result = await conn.execute(text(sql))
#             rows = [dict(row._mapping) for row in result]
#
#         raw_string = str(rows)
#
#         try:
#             return ast.literal_eval(raw_string)
#         except (ValueError, SyntaxError):
#             return ast.literal_eval(raw_string)
#
#     def _create_tools(self) -> list[BaseTool]:
#
#
#         db_tools =  [
#             QuerySQLDatabaseTool(db=self.db),
#             InfoSQLDatabaseTool(db=self.db),
#             ListSQLDatabaseTool(db=self.db),
#         ]
#
#         if self.llm is not None:
#             db_tools.append(QuerySQLCheckerTool(llm=self.llm, db=self.db))
#
#         return db_tools
#
#
#     def get_sql_tools(self) -> list[BaseTool]:
#         return self.toolkit

_READ_ONLY_START = {"select", "with", "explain"}
_BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|merge|call|copy)\b",
    re.IGNORECASE,
)

class AsyncWMSSQLService:
    def __init__(
            self
    ):
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