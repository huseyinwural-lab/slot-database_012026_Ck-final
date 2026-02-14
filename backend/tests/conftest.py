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
from app.utils import auth_player as auth_player_module
from app.utils.auth import create_access_token

# ✅ Karar: Test Hedefi Belirleme
# CI ortamında TARGET_URL set edilir, lokalde None kalır.
TARGET_URL = os.getenv("TEST_TARGET_URL", None)
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_casino.db"))
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

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
    # Eğer unit/integration testi yapılıyorsa SQLite kullan
    if not TARGET_URL:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    
    engine = create_async_engine(TEST_DB_URL, future=True)

    async def _init():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    if not TARGET_URL: # Sadece lokal testlerde DB init yap
        event_loop.run_until_complete(_init())

    yield engine
    event_loop.run_until_complete(engine.dispose())
    if not TARGET_URL and os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest_asyncio.fixture(scope="function")
async def client(async_session_factory):
    if TARGET_URL:
        # ✅ Karar: Acceptance Modu - Canlı container'a bağlan
        async with AsyncClient(base_url=TARGET_URL) as c:
            yield c
    else:
        # ✅ Unit/Integration Modu - In-process Mocking
        app.dependency_overrides[get_session] = lambda: async_session_factory()
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as c:
            yield c
        app.dependency_overrides.clear()

# --- Seed Helpers (Aynen Korundu) ---
# ... (Orijinal yardımcı fonksiyonlarını (create_tenant, admin_token vb.) buraya ekleyebilirsin)
