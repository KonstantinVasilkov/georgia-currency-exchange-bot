from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from src.config.settings import settings
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from typing import AsyncGenerator


def get_engine():
    """
    Create and return a SQLAlchemy engine.
    Uses the database URL from settings, which defaults to SQLite if not specified.
    """
    # Get the database URL from settings
    database_url = settings.DATABASE_URL

    # Create the engine with echo=True for development to see SQL queries
    # In production, this should be set to False
    engine = create_engine(database_url, echo=settings.DEBUG)

    return engine


# Create a sessionmaker that will be used to get database sessions
def get_session():
    """
    Get a database session.
    This function should be used as a dependency in FastAPI endpoints.
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    This function can be used with 'with' statements to ensure proper session handling.

    Example:
        with get_db_session() as session:
            # Use session

    Returns:
        A database session that will be automatically closed after the with block.
    """
    engine = get_engine()
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Function to create all tables defined in SQLModel models
def create_db_and_tables():
    """
    Create all tables defined in SQLModel models.
    This should be called when the application starts.
    """
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_async_engine():
    """
    Create and return an async SQLAlchemy engine.
    Uses the database URL from settings, which defaults to SQLite if not specified.
    """
    database_url = settings.DATABASE_URL
    if database_url.startswith("sqlite"):
        # SQLite async driver
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(database_url, echo=settings.DEBUG, future=True)
    return engine


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator for database session (for FastAPI dependency injection).
    """
    engine = get_async_engine()
    async with AsyncSession(engine) as session:
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
        self.session = AsyncSession(self.engine)
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        if self.session is not None:
            await self.session.close()
