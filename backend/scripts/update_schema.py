import asyncio
from sqlmodel import SQLModel
from app.core.database import engine

async def reinit_db():
    print("🔄 Re-initializing Database Schema...")
    async with engine.begin() as conn:
        # Re-create tables to include new models (GameConfigVersion, etc.)
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ Schema Updated.")

if __name__ == "__main__":
    asyncio.run(reinit_db())
