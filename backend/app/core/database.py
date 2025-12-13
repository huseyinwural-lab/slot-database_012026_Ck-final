from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from config import settings

# Create Async Engine
# The echo parameter helps with debugging SQL queries
engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)

async def init_db():
    """
    Creates tables if they don't exist.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Uncomment to reset DB (Dev only)
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """
    Dependency for FastAPI Routes to get a DB session.
    """
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
