from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from sqlalchemy import create_engine, text
from config import settings
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    QuerySQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
)

class WmsSqlTool:
    def __init__(self, query_check_llm: BaseChatModel):
        self.llm = query_check_llm
        self.db = self._create_database()
        self.toolkit = self._create_tools()

    def _create_engine_with_pooling(self):
        return create_engine(
            url=settings.DATABASE_URL.get_secret_value(),
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            connect_args={
                "options": f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT}"
            },
            execution_options={"postgresql_readonly": True}
        )

    def _create_database(self) -> SQLDatabase:
        return SQLDatabase(
            engine = self._create_engine_with_pooling(),
            include_tables = settings.SQL_TABLES,
            sample_rows_in_table_info=3,
            schema=settings.DB_SCHEMA,
        )

    # def run_query(self, sql: str) -> str:
    #     """Run SQL with column names included."""
    #     raw_string =  self.db.run(sql, include_columns=True)
    #
    #     try:
    #         return ast.literal_eval(raw_string)
    #     except (ValueError, SyntaxError):
    #         return ast.literal_eval(raw_string)

    def run_query(self, sql: str) -> list[dict]:
        """Run SQL and return rows as list of dicts."""
        with self.db._engine.connect() as conn:
            result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result]

    def _create_tools(self) -> list[BaseTool]:


        db_tools =  [
            QuerySQLDatabaseTool(db=self.db),
            InfoSQLDatabaseTool(db=self.db),
            ListSQLDatabaseTool(db=self.db),
        ]

        if self.llm is not None:
            db_tools.append(QuerySQLCheckerTool(llm=self.llm, db=self.db))

        return db_tools


    def get_sql_tools(self) -> list[BaseTool]:
        return self.toolkit



