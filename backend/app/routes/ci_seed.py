from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models.game_models import Game
from app.models.robot_models import RobotDefinition

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

    # Robot
    stmt = select(RobotDefinition).where(RobotDefinition.name == "Classic 777")
    robot = (await session.execute(stmt)).scalars().first()
    if not robot:
        robot = RobotDefinition(
            name="Classic 777",
            schema_version="1.0",
            config={"preset": "classic777", "lines": 20},
            config_hash="ci_seed_classic777",
            is_active=True,
        )
        session.add(robot)

    await session.commit()

    return {
        "seeded": True,
        "tenant_id": tenant_id,
        "game_external_id": "classic777",
        "robot_name": "Classic 777",
    }
