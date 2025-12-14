"""API key utilities.

Bu modül daha önce MongoDB (motor) üzerinden API key lookup yapıyordu.
PostgreSQL/SQLModel geçişi kapsamında runtime'da motor ihtiyacını kaldırmak için
Mongo kısımları söküldü.

Not: API key auth layer'i tekrar aktif edilecekse, SQLModel tarafında bir APIKey tablosu
(veya merkezi bir model) ile yeniden uygulanmalıdır.
"""

import secrets
from typing import List, Optional

from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.constants.api_keys import API_KEY_SCOPES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key() -> tuple[str, str, str]:
    """Generate a random API key and return (full_key, key_prefix, key_hash)."""
    full_key = secrets.token_urlsafe(32)
    key_prefix = full_key[:8]
    key_hash = pwd_context.hash(full_key)
    return full_key, key_prefix, key_hash


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
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


async def get_admin_api_key(*_args, **_kwargs) -> Optional[object]:
    """Deprecated: Mongo-based lookup removed."""
    raise NotImplementedError("Mongo-based API key lookup removed; SQL implementation not available")
