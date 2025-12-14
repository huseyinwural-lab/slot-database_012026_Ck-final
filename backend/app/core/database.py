from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from config import settings
import logging

logger = logging.getLogger(__name__)

# Create Async Engine
# The echo parameter helps with debugging SQL queries
# Note: For SQLite, we must use check_same_thread=False for async
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}

# Connection pool tuning (only meaningful for Postgres/asyncpg)
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

async def init_db():
    """DB şema init.

    - PostgreSQL (ve yeni DB'ler): create_all yeterlidir.
    - SQLite dosya DB (dev/preview): create_all mevcut tablolara yeni kolon eklemez.
      Bu nedenle **debug modunda** sqlite kullanıyorsak tabloları drop_all + create_all
      ile yeniden yaratıyoruz.

    Prod için hedef: Alembic migration (Patch 2).
    """

    try:
        async with engine.begin() as conn:
            env = getattr(settings, "env", "dev")

            # Safety barrier: drop_all is ONLY allowed in dev/local + DEBUG + sqlite.
            if (
                settings.debug
                and env in {"dev", "local"}
                and "sqlite" in (settings.database_url or "")
            ):
                logger.warning("SQLite + DEBUG + env=%s: resetting schema with drop_all/create_all", env)
                await conn.run_sync(SQLModel.metadata.drop_all)
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

# LEGACY MONGO WRAPPER SHIM (To prevent ImportErrors in unrefactored files)
class LegacyDBWrapper:
    def __getattr__(self, name):
        raise NotImplementedError(f"MongoDB wrapper is deprecated. Use SQLModel session. Accessing: {name}")

db_wrapper = LegacyDBWrapper()
