import asyncio
import os
from sqlalchemy.future import select
from app.core.database import async_session
from app.models.sql_models import Tenant

async def fix_tenant():
    async with async_session() as session:
        # Fetch default tenant
        result = await session.execute(select(Tenant).where(Tenant.id == "default_casino"))
        tenant = result.scalars().first()
        
        if tenant:
            print(f"Updating features for tenant: {tenant.name} ({tenant.id})")
            
            # Full feature set for Owner
            features = {
                "can_manage_admins": True,
                "can_view_reports": True,
                "can_manage_experiments": True,
                "can_use_kill_switch": True,
                "can_manage_affiliates": True,
                "can_use_crm": True,
                "can_use_game_robot": True,
                "can_manage_kyc": True,
                "can_manage_bonus": True,
                # Add any others just in case, though these cover menu.js
            }
            
            tenant.features = features
            session.add(tenant)
            await session.commit()
            print("✅ Tenant features updated successfully.")
        else:
            print("❌ Tenant 'default_casino' not found!")

if __name__ == "__main__":
    asyncio.run(fix_tenant())
