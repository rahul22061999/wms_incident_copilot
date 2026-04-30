from config import BASE_DIR

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy.orm import DeclarativeBase

DB_PATH = BASE_DIR / "audit.db"

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)