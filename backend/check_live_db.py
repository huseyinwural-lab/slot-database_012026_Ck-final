import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.utils.auth import verify_password

# Check the ACTUAL live DB
DB_URL = "sqlite+aiosqlite:////app/backend/casino.db"

async def check():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        print(f"Checking DB: {DB_URL}")
        try:
            result = await conn.execute(text("SELECT email, password_hash FROM adminuser"))
            rows = result.fetchall()
            print(f"Total AdminUsers: {len(rows)}")
            for row in rows:
                email, pwd_hash = row
                print(f"User: {email}")
                is_valid = verify_password("Admin123!", pwd_hash)
                print(f"Password 'Admin123!' valid? {is_valid}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
