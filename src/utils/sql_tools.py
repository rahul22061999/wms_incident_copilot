from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from sqlalchemy import create_engine
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

    def _create_tools(self) -> list[BaseTool]:
        db = self._create_database()

        db_tools =  [
            QuerySQLDatabaseTool(db=db),
            InfoSQLDatabaseTool(db=db),
            ListSQLDatabaseTool(db=db),
        ]

        if self.llm is not None:
            db_tools.append(QuerySQLCheckerTool(llm=self.llm, db=db))

        return db_tools

    def get_sql_tools(self) -> list[BaseTool]:
        return self.toolkit



