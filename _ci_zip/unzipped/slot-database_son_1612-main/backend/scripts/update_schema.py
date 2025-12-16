import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, SQLModel
from app.core.database import engine
from app.models.sql_models import Game, GameConfigVersion

async def reinit_db():
    print("🔄 Re-initializing Database Schema...")
    async with engine.begin() as conn:
        # Re-create tables to include new models (GameConfigVersion, etc.)
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ Schema Updated.")

if __name__ == "__main__":
    asyncio.run(reinit_db())
