import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select
from app.models.sql_models import AdminUser
from app.utils.auth import verify_password

# Use the same DB URL as the app
DB_URL = "sqlite+aiosqlite:///./casino.db"

async def check():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        # Raw SQL to check table content first
        from sqlalchemy import text
        result = await conn.execute(text("SELECT email, password_hash FROM adminuser"))
        rows = result.fetchall()
        print(f"Total AdminUsers: {len(rows)}")
        for row in rows:
            email, pwd_hash = row
            print(f"User: {email}")
            print(f"Hash: {pwd_hash}")
            is_valid = verify_password("Admin123!", pwd_hash)
            print(f"Password 'Admin123!' valid? {is_valid}")

if __name__ == "__main__":
    asyncio.run(check())
