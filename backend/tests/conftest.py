import os
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

sys.path.append(os.path.abspath("/app/backend"))

from config import settings
from app.core.database import engine, async_session
from app.models.sql_models import Player, Tenant
from server import app


@pytest.fixture(scope="session")
def db_engine():
    # Use the same engine as the app (sqlite test db)
    return engine


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    async_session_local = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_local() as session:
        # Ensure tables exist
        await db_engine.begin()
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


async def _create_tenant(session: AsyncSession, name: str = "Test Casino") -> Tenant:
    tenant = Tenant(name=name, type="owner", features={})
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant


async def _create_player(
    session: AsyncSession,
    tenant_id: str,
    email: str = "player@test.com",
    username: str = "player",
    kyc_status: str = "verified",
    balance_available: float = 0.0,
    balance_held: float = 0.0,
) -> Player:
    player = Player(
        tenant_id=tenant_id,
        email=email,
        username=username,
        password_hash="noop_hash",
        balance_real_available=balance_available,
        balance_real_held=balance_held,
        kyc_status=kyc_status,
        registered_at=datetime.utcnow(),
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


def _make_player_token(player: Player, tenant_id: str) -> str:
    payload = {
        "sub": player.id,
        "tenant_id": tenant_id,
        "role": "player",
        "exp": datetime.utcnow() + timedelta(days=1),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


@pytest.fixture
async def player_with_token(db_session):
    tenant = await _create_tenant(db_session)
    player = await _create_player(db_session, tenant_id=tenant.id)
    token = _make_player_token(player, tenant.id)
    return tenant, player, token
