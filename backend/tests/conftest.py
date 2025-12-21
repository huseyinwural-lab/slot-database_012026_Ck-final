import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from config import settings
from server import app
from app.models.sql_models import Player, Tenant
from app.core.database import get_session
from app.utils.auth_player import get_current_player
from fastapi import Request, HTTPException
from jose import jwt, JWTError


TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "test_casino.db")
TEST_DB_URL = f"sqlite:///{os.path.abspath(TEST_DB_PATH)}"


@pytest.fixture(scope="session")
def sync_engine():
    # Temiz test DB'si ile başla
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        future=True,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(sync_engine):
    SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def make_override_get_current_player(db_session):
    def _override(request: Request):
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

        player = db_session.get(Player, player_id)
        if not player:
            raise HTTPException(status_code=401, detail="Player not found")
        return player

    return _override


@pytest.fixture(scope="function")
def client(db_session):
    # Sadece auth dependency'sini override et; DB async yapısı uygulamada aynı kalır.
    app.dependency_overrides[get_current_player] = make_override_get_current_player(db_session)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def create_tenant(db, name: str = "Test Casino", ttype: str = "owner") -> Tenant:
    tenant = Tenant(name=name, type=ttype, features={})
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_player(
    db,
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
        registered_at=datetime.now(timezone.utc),
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def make_player_token(player_id: str, tenant_id: str) -> str:
    payload = {
        "sub": player_id,
        "tenant_id": tenant_id,
        "role": "player",
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.fixture
def player_with_token(db_session):
    tenant = create_tenant(db_session)
    player = create_player(db_session, tenant_id=tenant.id)
    token = make_player_token(player.id, tenant.id)
    return tenant, player, token
