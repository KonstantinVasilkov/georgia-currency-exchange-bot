from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from typing import AsyncGenerator
from src.config.settings import settings


def get_async_engine():
    """
    Create and return an async SQLAlchemy engine.
    Uses the database URL from settings, which defaults to SQLite if not specified.
    """
    database_url = settings.DATABASE_URL
    if database_url.startswith("sqlite"):
        # SQLite async driver
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(database_url, echo=False, future=True)
    return engine


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator for database session (for FastAPI dependency injection).
    """
    engine = get_async_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


class async_get_db_session:
    """
    Async context manager for database sessions.
    Usage:
        async with async_get_db_session() as session:
            ...
    """

    def __init__(self):
        self.engine = get_async_engine()
        self.session = None

    async def __aenter__(self):
        self.session = AsyncSession(self.engine, expire_on_commit=False)
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        if self.session is not None:
            await self.session.close()
