import os
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import Request, HTTPException, Depends
from httpx import AsyncClient
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel, select

from config import settings
from server import app
from app.core.database import get_session
from app.models.sql_models import Tenant, Player, AdminUser
from app.models.discount import Discount
from app.utils import auth_player as auth_player_module
from app.utils.auth import create_access_token

# ✅ Karar 1: CI ortamında Postgres, lokalde SQLite kullanabilen esnek URL
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test_casino.db'))}")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

@pytest.fixture(scope="session")
def async_engine(event_loop):
    # Eğer SQLite kullanılıyorsa temizle
    if "sqlite" in DATABASE_URL:
        db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        if os.path.exists(db_path):
            os.remove(db_path)

    engine = create_async_engine(DATABASE_URL, future=True)

    async def _init():
        async with engine.begin() as conn:
            # ✅ Her koşuda temiz DB şeması
            await conn.run_sync(SQLModel.metadata.create_all)

    event_loop.run_until_complete(_init())
    yield engine
    event_loop.run_until_complete(engine.dispose())

@pytest.fixture(scope="session")
def async_session_factory(async_engine):
    return async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(scope="session", autouse=True)
def _patch_global_db(async_engine):
    import app.core.database as db
    db.engine = async_engine
    db.async_session = async_sessionmaker(db.engine, expire_on_commit=False, class_=AsyncSession)
    settings.database_url = DATABASE_URL
    os.environ["DATABASE_URL"] = DATABASE_URL

# --- Dependency Overrides ---
def make_override_get_session(async_session_factory):
    async def _override():
        async with async_session_factory() as session:
            yield session
    return _override

@pytest_asyncio.fixture(scope="function")
async def client(async_session_factory):
    app.dependency_overrides[get_session] = make_override_get_session(async_session_factory)
    if get_current_player in app.dependency_overrides:
        app.dependency_overrides.pop(get_current_player)
    auth_player_module.get_session = get_session
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()

# --- Seed Helpers (Verdiğin orijinal yardımcılar) ---
async def _create_tenant(session: AsyncSession, name="Test Casino", ttype="owner") -> Tenant:
    result = await session.execute(select(Tenant).where(Tenant.name == name))
    tenant = result.scalars().first()
    if tenant: return tenant
    tenant = Tenant(name
