import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_audit():
    engine = create_async_engine("sqlite+aiosqlite:////app/backend/casino.db")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT action, resource_type, result, details FROM auditlog ORDER BY timestamp DESC LIMIT 10"))
        print(f"{'ACTION':<20} | {'TYPE':<15} | {'RESULT':<10} | {'DETAILS'}")
        print("-" * 80)
        for row in result:
            print(f"{row[0]:<20} | {row[1]:<15} | {row[2]:<10} | {row[3]}")

if __name__ == "__main__":
    asyncio.run(check_audit())