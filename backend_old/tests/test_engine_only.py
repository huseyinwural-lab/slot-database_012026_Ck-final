import asyncio
import sys
import os

# Set path manually
sys.path.append(os.path.abspath("/app/backend"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
# Do not import app.models.sql_models here to isolate connection issue
# Define minimal models here to test engine connectivity first

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

async def test_engine():
    print("🚀 Testing Engine Connection...")
    try:
        engine = create_async_engine(TEST_DB_URL, echo=False)
        async with engine.connect() as conn:
            # Simple query
            await conn.execute(select(1))
        print("   ✅ Engine Connected")
    except Exception as e:
        print(f"   ❌ Engine Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_engine())
