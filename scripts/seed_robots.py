import asyncio
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from app.models.robot_models import RobotDefinition, MathAsset, GameRobotBinding
from app.models.game_models import Game
from sqlmodel import select
from app.models.sql_models import Tenant

async def seed_robots():
    print("=== Seeding Robots & Math Assets ===")
    
    async with async_session() as session:
        # 1. Define Math Assets (Reelset & Paytable)
        # Simplified 3x3 Slot Machine
        
        # Paytable: Symbol -> Multiplier (3 match)
        # 0: Cherry (x5), 1: Lemon (x10), 2: Seven (x50), 3: Diamond (x100)
        paytable_content = {
            "0": 5, "1": 10, "2": 50, "3": 100
        }
        
        # Reelset: 3 Reels, each is a list of symbol IDs
        # Weighting: 0 is common, 3 is rare
        reelset_content = {
            "reels": [
                [0, 0, 0, 1, 1, 2, 0, 1, 3, 0], # Reel 1
                [0, 0, 1, 1, 0, 2, 0, 1, 0, 3], # Reel 2
                [0, 0, 1, 0, 0, 2, 1, 0, 0, 3]  # Reel 3
            ]
        }
        
        assets = [
            MathAsset(
                ref_key="basic_pay_v1",
                type="paytable",
                content=paytable_content,
                content_hash=hashlib.sha256(json.dumps(paytable_content).encode()).hexdigest()
            ),
            MathAsset(
                ref_key="basic_reels_v1",
                type="reelset",
                content=reelset_content,
                content_hash=hashlib.sha256(json.dumps(reelset_content).encode()).hexdigest()
            )
        ]
        
        # Upsert Assets
        for asset in assets:
            stmt = select(MathAsset).where(MathAsset.ref_key == asset.ref_key)
            existing = (await session.execute(stmt)).scalars().first()
            if not existing:
                session.add(asset)
                print(f"[+] Added Asset: {asset.ref_key}")
            else:
                print(f"[.] Asset exists: {asset.ref_key}")
        
        await session.flush()
        
        # 2. Define Robot
        robot_config = {
            "paytable_ref": "basic_pay_v1",
            "reelset_ref": "basic_reels_v1",
            "lines": 1 # Single line for MVP
        }
        
        robot = RobotDefinition(
            name="Classic 777 Engine",
            config=robot_config,
            config_hash=hashlib.sha256(json.dumps(robot_config).encode()).hexdigest()
        )
        
        # Upsert Robot
        stmt_robot = select(RobotDefinition).where(RobotDefinition.name == robot.name)
        existing_robot = (await session.execute(stmt_robot)).scalars().first()
        
        if not existing_robot:
            session.add(robot)
            await session.flush()
            print(f"[+] Added Robot: {robot.name}")
            robot_id = robot.id
        else:
            print(f"[.] Robot exists: {robot.name}")
            robot_id = existing_robot.id
            
        # 3. Bind to Game
        # Find "Classic 777" game created in Sprint B
        stmt_game = select(Game).where(Game.external_id == "classic777")
        game = (await session.execute(stmt_game)).scalars().first()
        
        if game:
            stmt_bind = select(GameRobotBinding).where(GameRobotBinding.game_id == game.id)
            existing_bind = (await session.execute(stmt_bind)).scalars().first()
            
            if not existing_bind:
                binding = GameRobotBinding(
                    tenant_id=game.tenant_id,
                    game_id=game.id,
                    robot_id=robot_id,
                    is_enabled=True
                )
                session.add(binding)
                print(f"[+] Bound Robot to Game: {game.title}")
            else:
                print(f"[.] Binding exists for: {game.title}")
        else:
            print("[WARN] Game 'Classic 777' not found. Skipping binding.")
            
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_robots())
