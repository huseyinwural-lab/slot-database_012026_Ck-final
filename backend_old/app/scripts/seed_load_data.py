import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.game_models import Game
from app.models.sql_models import Player, Tenant
import os
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:////app/backend/casino.db")

async def seed_data():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Tenant
        tenant = Tenant(id="default_tenant", name="Default", type="owner")
        session.add(tenant)
        try:
            await session.commit()
        except:
            await session.rollback()

        # 2. Game
        game = Game(id="load_game_1", tenant_id="default_tenant", provider_id="pragmatic", external_id="load_game_1", name="Load Test Game")
        session.add(game)
        try:
            await session.commit()
        except:
            await session.rollback()
            
        # 3. Users
        for i in range(10): # 10 users for load test
            uid = f"load_user_{i}"
            # Check if exists
            p = await session.get(Player, uid)
            if not p:
                p = Player(
                    id=uid,
                    tenant_id="default_tenant",
                    username=uid,
                    email=f"{uid}@test.com",
                    password_hash="pw",
                    balance_real_available=10000.0
                )
                session.add(p)
        try:
            await session.commit()
        except:
            await session.rollback()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())
