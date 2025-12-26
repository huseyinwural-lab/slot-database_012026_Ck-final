import asyncio
import os
from config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import SQLModel, get_session
from app.models.game_models import Game

# Ensure DB path matches where we are writing
print(f"DB URL: {settings.database_url}")

async def seed_games_direct():
    engine = create_async_engine(settings.database_url)
    
    # 1. Create Tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Tables created.")

    # 2. Seed
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check existing
        from sqlmodel import select
        existing = (await session.execute(select(Game))).scalars().first()
        if existing:
            print("Games already seeded.")
            return

        games = [
            Game(
                tenant_id="default_casino",
                provider_id="pragmatic",
                external_id="vs20doghouse",
                title="The Dog House",
                type="slot",
                image_url="https://www.pragmaticplay.com/wp-content/uploads/2019/05/The-Dog-House-960x640.jpg"
            ),
            Game(
                tenant_id="default_casino",
                provider_id="pragmatic",
                external_id="vs20olympus",
                title="Gates of Olympus",
                type="slot",
                image_url="https://www.pragmaticplay.com/wp-content/uploads/2021/01/Gates-of-Olympus-960x640.jpg"
            ),
            Game(
                tenant_id="default_casino",
                provider_id="evolution",
                external_id="crazytime",
                title="Crazy Time",
                type="live",
                image_url="https://evolution.com/wp-content/uploads/2020/06/Crazy-Time-Evolution-Gaming.jpg"
            ),
            Game(
                tenant_id="default_casino",
                provider_id="mock",
                external_id="classic777",
                title="Classic 777",
                type="slot",
                image_url="" # Fallback to icon
            )
        ]
        
        session.add_all(games)
        await session.commit()
        print(f"Seeded {len(games)} games.")

if __name__ == "__main__":
    asyncio.run(seed_games_direct())
