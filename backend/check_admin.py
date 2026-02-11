import asyncio
import os
from sqlalchemy.future import select
from app.core.database import async_session
from app.models.sql_models import AdminUser, Tenant
from app.utils.auth import get_password_hash

async def check_admin():
    async with async_session() as session:
        # Check Tenant first
        result = await session.execute(select(Tenant).where(Tenant.id == "default_casino"))
        tenant = result.scalars().first()
        if not tenant:
            print("Creating default tenant...")
            tenant = Tenant(id="default_casino", name="Default Casino", type="owner")
            session.add(tenant)
            await session.commit()

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
