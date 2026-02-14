import asyncio
from datetime import datetime
from sqlmodel import select
from app.core.database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.sql_models import Game, Tenant
import uuid

async def seed_games_sql():
    print("🚀 Seeding Games into PostgreSQL...")
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Get Tenant ID (Default Casino)
        stmt = select(Tenant).where(Tenant.name == "Default Casino")
        result = await session.execute(stmt)
        tenant = result.scalars().first()
        
        if not tenant:
            print("⚠️ Default Casino Tenant not found! Creating one...")
            tenant = Tenant(name="Default Casino", type="owner")
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            print(f"✅ Created Tenant: {tenant.id}")
        
        tenant_id = tenant.id

        # 2. Define Games
        games_data = [
            {"name": "Sweet Bonanza", "provider": "Pragmatic Play", "category": "Slot", "rtp": 96.5},
            {"name": "Gates of Olympus", "provider": "Pragmatic Play", "category": "Slot", "rtp": 96.5},
            {"name": "Starburst", "provider": "NetEnt", "category": "Slot", "rtp": 96.1},
            {"name": "Book of Dead", "provider": "NetEnt", "category": "Slot", "rtp": 96.2},
            {"name": "Lightning Roulette", "provider": "Evolution", "category": "Live", "rtp": 97.3},
            {"name": "Crazy Time", "provider": "Evolution", "category": "Live", "rtp": 95.5},
            {"name": "Aviator", "provider": "Spribe", "category": "Crash", "rtp": 97.0},
        ]

        count = 0
        for g in games_data:
            # Check if exists
            exists_stmt = select(Game).where(Game.name == g["name"]).where(Game.tenant_id == tenant_id)
            existing = (await session.execute(exists_stmt)).scalars().first()
            
            if not existing:
                new_game = Game(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    name=g["name"],
                    provider=g["provider"],
                    category=g["category"],
                    status="active",
                    rtp=g["rtp"],
                    image_url=f"https://placehold.co/300x200?text={g['name'].replace(' ', '+')}",
                    configuration={"min_bet": 0.2, "max_bet": 100},
                    created_at=datetime.utcnow()
                )
                session.add(new_game)
                count += 1
        
        await session.commit()
        print(f"✅ Seeded {count} games.")

if __name__ == "__main__":
    asyncio.run(seed_games_sql())
