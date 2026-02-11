import asyncio
import os
from sqlalchemy.future import select
from app.core.database import async_session
from app.models.sql_models import AdminUser
from app.infra.utils import hash_password # wait, I might have replaced this import in test_ops but need to check where it is.
# Actually I replaced it in test_ops.py. Let's see where hash_password really is.
# routes/player_auth.py used app.utils.auth.get_password_hash. 
# Let's use that.
from app.utils.auth import get_password_hash

async def check_admin():
    async with async_session() as session:
        result = await session.execute(select(AdminUser).where(AdminUser.email == "admin@casino.com"))
        user = result.scalars().first()
        
        if user:
            print(f"Admin Found: {user.email}, ID: {user.id}")
        else:
            print("Admin NOT Found. Creating...")
            # Create Default Admin
            admin = AdminUser(
                email="admin@casino.com",
                username="admin",
                full_name="System Admin",
                role="superadmin",
                tenant_id="default_casino",
                password_hash=get_password_hash("Admin123!"),
                is_platform_owner=True,
                status="active",
                is_active=True
            )
            session.add(admin)
            await session.commit()
            print("Admin Created.")

if __name__ == "__main__":
    asyncio.run(check_admin())
