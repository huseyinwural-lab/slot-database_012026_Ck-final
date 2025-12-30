import os
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import Request, HTTPException, Depends
from fastapi.testclient import TestClient
from httpx import AsyncClient
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel, select

from config import settings
from server import app
from app.core.database import get_session
from app.models.sql_models import Tenant, Player, AdminUser
from app.utils.auth_player import get_current_player
from app.utils.auth import create_access_token


# ------------------------------------------------------------
# AsyncIO loop discipline
# ------------------------------------------------------------
# In CI, pytest can create a new event loop per test. If an AsyncEngine is created
# on a different loop (e.g. via asyncio.run), asyncpg/SQLAlchemy can raise:
#   "got Future ... attached to a different loop"
# A session-scoped loop prevents cross-loop reuse.
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


def _run(coro):
    # Run a coroutine on the session-scoped event loop to avoid cross-loop issues.
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


# ---------- Test DB (async sqlite) ----------
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_casino.db"))
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def async_engine(event_loop):
    # Her test koşusunda temiz DB
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    engine = create_async_engine(TEST_DB_URL, future=True)

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    event_loop.run_until_complete(_init())

    yield engine

    # Cleanup
    event_loop.run_until_complete(engine.dispose())
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="session")
def async_session_factory(async_engine):
    return async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


# ---------- Dependency overrides ----------

def make_override_get_session(async_session_factory):
    async def _override():
        async with async_session_factory() as session:
            yield session

    return _override


def override_get_current_player_factory():
    async def _override(request: Request, session: AsyncSession = Depends(get_session)):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        player_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not player_id or not tenant_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        player = await session.get(Player, player_id)
        if not player:
            raise HTTPException(status_code=401, detail="Player not found")
        return player

    return _override


@pytest_asyncio.fixture(scope="function")
async def client(async_session_factory):
    # Override DB session provider
    app.dependency_overrides[get_session] = make_override_get_session(async_session_factory)
    # Override auth so it loads Player via SAME AsyncSession
    app.dependency_overrides[get_current_player] = override_get_current_player_factory()

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

    app.dependency_overrides.clear()


# ---------- Seed helpers ----------


async def _create_tenant(session: AsyncSession, name="Test Casino", ttype="owner") -> Tenant:
    # Try find existing tenant by name to avoid UNIQUE constraint issues in tests
    from sqlmodel import select

    result = await session.execute(select(Tenant).where(Tenant.name == name))
    tenant = result.scalars().first()
    if tenant:
        return tenant

    tenant = Tenant(name=name, type=ttype, features={})
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)
    return tenant


async def _create_player(
    session: AsyncSession,
    tenant_id: str,
    email="player@test.com",
    username="player",
    kyc_status="verified",
    balance_available=0.0,
    balance_held=0.0,
) -> Player:
    player = Player(
        tenant_id=tenant_id,
        email=email,
        username=username,
        password_hash="noop_hash",
        balance_real_available=balance_available,
        balance_real_held=balance_held,
        kyc_status=kyc_status,
        registered_at=datetime.now(timezone.utc),
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


def _make_player_token(player_id: str, tenant_id: str) -> str:
    payload = {
        "sub": player_id,
        "tenant_id": tenant_id,
        "role": "player",
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def _create_admin(
    session: AsyncSession,
    tenant_id: str,
    email="admin@test.com",
    username="admin",
    role="Admin",
    is_platform_owner=False,
) -> AdminUser:
    # Try find existing admin by email to avoid UNIQUE constraint issues in tests
    result = await session.execute(select(AdminUser).where(AdminUser.email == email))
    admin = result.scalars().first()
    if admin:
        return admin

    admin = AdminUser(
        tenant_id=tenant_id,
        username=username,
        email=email,
        full_name="Test Admin",
        password_hash="noop_hash",
        role=role,
        is_platform_owner=is_platform_owner,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


def _make_admin_token(admin_id: str, tenant_id: str, email: str) -> str:
    return create_access_token(
        data={"sub": admin_id, "email": email, "tenant_id": tenant_id, "role": "Admin"},
        expires_delta=timedelta(days=1)
    )


@pytest.fixture(scope="function")
def admin_token(async_session_factory):
    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            admin = await _create_admin(session, tenant_id=tenant.id)
            token = _make_admin_token(admin.id, tenant.id, admin.email)
            return token

    return _run(_seed())


@pytest.fixture(scope="function")
def session(async_session_factory):
    async def _get_session():
        async with async_session_factory() as session:
            return session

    return _run(_get_session())


@pytest.fixture(scope="function")
def player_with_token(async_session_factory):
    async def _seed():
        async with async_session_factory() as session:
            tenant = await _create_tenant(session)
            player = await _create_player(session, tenant_id=tenant.id)
            token = _make_player_token(player.id, tenant.id)
            return tenant, player, token

    return _run(_seed())
