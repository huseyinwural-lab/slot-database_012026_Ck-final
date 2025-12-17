from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create Async Engine
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

pool_size = int(getattr(settings, "db_pool_size", 5)) if hasattr(settings, "db_pool_size") else 5
max_overflow = int(getattr(settings, "db_max_overflow", 10)) if hasattr(settings, "db_max_overflow") else 10

try:
    engine_kwargs = {
        "echo": settings.debug,
        "future": True,
        "connect_args": connect_args,
    }

    if "postgresql" in (settings.database_url or ""):
        engine_kwargs.update({"pool_size": pool_size, "max_overflow": max_overflow})

    engine = create_async_engine(settings.database_url, **engine_kwargs)
except Exception as e:
    logger.critical(f"Failed to create database engine: {e}")
    raise


# Shared session factory (used by middleware/background tasks)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """DB Schema Init.
    
    Modified to NEVER drop tables automatically to prevent data loss during development reloads.
    """
    try:
        async with engine.begin() as conn:
            # We removed the drop_all logic here to persist data across reloads
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("Database initialized (create_all run).")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        raise

async def get_session() -> AsyncSession:
    """Dependency for FastAPI Routes to get a DB session."""
    async with async_session() as session:
        yield session
