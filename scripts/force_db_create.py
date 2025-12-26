import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import SQLModel
from config import settings

async def force_create_tables():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Tables created (Force)")

if __name__ == "__main__":
    asyncio.run(force_create_tables())
