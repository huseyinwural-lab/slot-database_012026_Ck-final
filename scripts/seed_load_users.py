import asyncio
import os
import secrets
from sqlmodel import select
from app.core.database import async_session
# Import all models to populate registry
from app.models.sql_models import Player, Tenant
from app.models.game_models import Game
from app.utils.auth import get_password_hash
from datetime import datetime

CONCURRENT_USERS = 50 # Match load test concurrency
PREFIX = "load_user_"

async def seed_load_users():
    print(f"Seeding {CONCURRENT_USERS} users for load test...")
    
    password_hash = get_password_hash("Password123!")
    
    async with async_session() as session:
        # Check tenant
        tenant = await session.get(Tenant, "default_casino")
        if not tenant:
            session.add(Tenant(id="default_casino", name="Default Casino", type="owner"))
            await session.commit()

        users = []
        for i in range(CONCURRENT_USERS):
            email = f"{PREFIX}{i}@load.test"
            username = f"{PREFIX}{i}"
            
            # Check existing
            existing = (await session.execute(select(Player).where(Player.email == email))).scalars().first()
            if not existing:
                user = Player(
                    email=email,
                    username=username,
                    password_hash=password_hash,
                    tenant_id="default_casino",
                    # Pre-verify
                    email_verified=True,
                    sms_verified=True,
                    kyc_status="verified",
                    # Pre-load balance
                    balance_real_available=10000.0,
                    balance_real_held=0.0,
                    registered_at=datetime.utcnow()
                )
                users.append(user)
        
        if users:
            session.add_all(users)
            await session.commit()
            print(f"Created {len(users)} users.")
        else:
            print("Users already seeded.")

if __name__ == "__main__":
    asyncio.run(seed_load_users())
