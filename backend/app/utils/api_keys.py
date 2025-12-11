import secrets
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

from app.constants.api_keys import API_KEY_SCOPES
from app.models.domain.admin import AdminAPIKey

# Create pwd_context locally to avoid circular import
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key() -> tuple[str, str, str]:
    """Generate a random API key and return (full_key, key_prefix, key_hash).

    full_key: raw secret that will be shown once
    key_prefix: first 8 chars, can be logged / shown in UI
    key_hash: bcrypt hash stored in DB
    """
    full_key = secrets.token_urlsafe(32)
    key_prefix = full_key[:8]
    key_hash = pwd_context.hash(full_key)
    return full_key, key_prefix, key_hash


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Verify a raw API key against stored bcrypt hash."""
    try:
        return pwd_context.verify(raw_key, stored_hash)
    except Exception:
        return False


def validate_scopes(scopes: List[str]) -> None:
    if not scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_API_KEY_SCOPE", "reason": "empty_scopes"},
        )
    invalid = [s for s in scopes if s not in API_KEY_SCOPES]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_API_KEY_SCOPE",
                "invalid_scopes": invalid,
                "allowed_scopes": API_KEY_SCOPES,
            },
        )


async def get_admin_api_key(db: AsyncIOMotorDatabase, raw_key: str) -> Optional[AdminAPIKey]:
    """Lookup and verify an AdminAPIKey by raw key.

    1) Use prefix for quick lookup
    2) Verify full key against bcrypt hash
    """
    if not raw_key:
        return None

    key_prefix = raw_key[:8]
    doc = await db.admin_api_keys.find_one({"key_prefix": key_prefix, "active": True}, {"_id": 0})
    if not doc:
        return None

    if not verify_api_key(raw_key, doc.get("key_hash", "")):
        return None

    # Update last_used_at best-effort (fire and forget)
    await db.admin_api_keys.update_one(
        {"id": doc.get("id")},
        {"$set": {"last_used_at": datetime.now(timezone.utc)}},
    )

    return AdminAPIKey(**doc)
