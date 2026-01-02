from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.game_models import Game
from app.models.robot_models import RobotDefinition, MathAsset, GameRobotBinding

router = APIRouter(prefix="/api/v1/ci", tags=["ci"])


@router.post("/seed")
async def ci_seed(session: AsyncSession = Depends(get_session)):
    """Deterministic seed for CI/E2E.

    Seeds required entities referenced by Playwright tests:
    - Game external_id=classic777
    - Robot name includes 'Classic 777'

    This is intentionally minimal and safe to re-run.
    """

    tenant_id = "default_casino"

    # Game
    stmt = select(Game).where(Game.tenant_id == tenant_id, Game.external_id == "classic777")
    game = (await session.execute(stmt)).scalars().first()
    if not game:
        game = Game(
            tenant_id=tenant_id,
            provider_id="mock",
            external_id="classic777",
            name="Classic 777",
            provider="mock",
            category="slot",
            status="active",
            is_active=True,
            configuration={"preset": "classic777"},
        )
        session.add(game)

    # Math assets + Robot + Binding (required for mock-provider spin)

    reel_ref = "classic777_reelset_v1"
    pay_ref = "classic777_paytable_v1"

    # Reelset asset
    stmt = select(MathAsset).where(MathAsset.ref_key == reel_ref)
    reel_asset = (await session.execute(stmt)).scalars().first()
    if not reel_asset:
        # Minimal 3-reel strip with symbols [0,1,2] repeated.
        reel_content = {
            "reels": [
                [0, 1, 2, 0, 1, 2, 0, 1, 2],
                [0, 1, 2, 0, 1, 2, 0, 1, 2],
                [0, 1, 2, 0, 1, 2, 0, 1, 2],
            ]
        }
        # Hash must match MathAsset schema
        import hashlib
        import json

        reel_hash = hashlib.sha256(json.dumps(reel_content, sort_keys=True).encode()).hexdigest()
        reel_asset = MathAsset(ref_key=reel_ref, type="reelset", version="1.0", content=reel_content, content_hash=reel_hash)
        session.add(reel_asset)

    # Paytable asset
    stmt = select(MathAsset).where(MathAsset.ref_key == pay_ref)
    pay_asset = (await session.execute(stmt)).scalars().first()
    if not pay_asset:
        pay_content = {
            "0": 5,
            "1": 10,
            "2": 20,
        }
        import hashlib
        import json

        pay_hash = hashlib.sha256(json.dumps(pay_content, sort_keys=True).encode()).hexdigest()
        pay_asset = MathAsset(ref_key=pay_ref, type="paytable", version="1.0", content=pay_content, content_hash=pay_hash)
        session.add(pay_asset)

    # Robot
    stmt = select(RobotDefinition).where(RobotDefinition.name == "Classic 777")
    robot = (await session.execute(stmt)).scalars().first()
    if not robot:
        robot_config = {
            "preset": "classic777",
            "lines": 20,
            "reelset_ref": reel_ref,
            "paytable_ref": pay_ref,
        }
        import hashlib
        import json

        robot_hash = hashlib.sha256(json.dumps(robot_config, sort_keys=True).encode()).hexdigest()
        robot = RobotDefinition(
            name="Classic 777",
            schema_version="1.0",
            config=robot_config,
            config_hash=robot_hash,
            is_active=True,
        )
        session.add(robot)

    await session.flush()

    # Ensure binding exists and enabled
    stmt = select(GameRobotBinding).where(
        GameRobotBinding.game_id == game.id,
        GameRobotBinding.robot_id == robot.id,
        GameRobotBinding.is_enabled,
    )
    binding = (await session.execute(stmt)).scalars().first()
    if not binding:
        binding = GameRobotBinding(
            tenant_id=tenant_id,
            game_id=game.id,
            robot_id=robot.id,
            is_enabled=True,
        )
        session.add(binding)

    await session.commit()

    return {
        "seeded": True,
        "tenant_id": tenant_id,
        "game_external_id": "classic777",
        "robot_name": "Classic 777",
    }
