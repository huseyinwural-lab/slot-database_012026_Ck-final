import asyncio
import os
from config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import SQLModel
from app.models.sql_models import * 
from app.models.game_models import *
from app.models.robot_models import *

# Ensure DB path matches
print(f"DB URL: {settings.database_url}")

async def force_create_tables_direct():
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Tables created (Direct Force).")

if __name__ == "__main__":
    asyncio.run(force_create_tables_direct())
