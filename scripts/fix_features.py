import asyncio
from sqlmodel import select
from app.core.database import async_session
from app.models.sql_models import Tenant

async def fix_tenant_features():
    async with async_session() as session:
        # 1. Update Default Casino
        t1 = await session.get(Tenant, "default_casino")
        if t1:
            t1.features["can_use_game_robot"] = True
            t1.features["can_manage_kyc"] = True
            t1.features["can_manage_bonus"] = True
            session.add(t1)
            print("Updated default_casino features")

        # 2. Update Demo Renter
        t2 = await session.get(Tenant, "demo_renter")
        if t2:
            t2.features["can_use_game_robot"] = True
            t2.features["can_manage_kyc"] = True
            t2.features["can_manage_bonus"] = True
            session.add(t2)
            print("Updated demo_renter features")
            
        await session.commit()

if __name__ == "__main__":
    asyncio.run(fix_tenant_features())
