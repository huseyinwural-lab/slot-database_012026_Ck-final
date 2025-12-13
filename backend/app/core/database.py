from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create Async Engine
# The echo parameter helps with debugging SQL queries
# Note: For SQLite, we must use check_same_thread=False for async
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

try:
    engine = create_async_engine(
        settings.database_url, 
        echo=settings.debug, 
        future=True,
        connect_args=connect_args
    )
except Exception as e:
    logger.critical(f"Failed to create database engine: {e}")
    raise

async def init_db():
    """
    Creates tables if they don't exist.
    In production, use Alembic migrations instead.
    """
    try:
        async with engine.begin() as conn:
            # await conn.run_sync(SQLModel.metadata.drop_all) # Uncomment to reset DB (Dev only)
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database initialized and tables created.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        raise

async def get_session() -> AsyncSession:
    """
    Dependency for FastAPI Routes to get a DB session.
    """
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
