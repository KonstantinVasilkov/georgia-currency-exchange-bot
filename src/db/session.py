from sqlmodel import SQLModel, create_engine, Session
from src.config.settings import settings

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

# Function to create all tables defined in SQLModel models
def create_db_and_tables():
    """
    Create all tables defined in SQLModel models.
    This should be called when the application starts.
    """
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
