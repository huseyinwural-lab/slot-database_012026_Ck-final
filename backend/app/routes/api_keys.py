from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, Body, Request
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.core.errors import AppError
from app.models.sql_models import APIKey
from app.utils.auth import get_current_admin, AdminUser
from app.utils.tenant import get_current_tenant_id
from app.constants.api_keys import API_KEY_SCOPES
from app.schemas.api_keys import APIKeyPublic, APIKeyCreatedOnce
from app.services.audit import audit

router = APIRouter(prefix="/api/v1/api-keys", tags=["api_keys"])


@router.get("/scopes", response_model=List[str])
async def get_scopes():
    # Frontend expects array of strings
    return API_KEY_SCOPES


@router.get("/", response_model=List[APIKeyPublic])
async def get_api_keys(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = select(APIKey).where(APIKey.tenant_id == tenant_id)
    result = await session.execute(query)
    keys = result.scalars().all()

    # Never return key_hash
    return [
        APIKeyPublic(
            id=k.id,
            tenant_id=k.tenant_id,
            name=k.name,
            scopes=(k.scopes.split(",") if k.scopes else []),
            active=(k.status == "active"),
            created_at=k.created_at,
            last_used_at=None,
        )
        for k in keys
    ]


@router.post("/", response_model=APIKeyCreatedOnce)
async def create_api_key(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Lightweight SQL-only impl for UI: generate a secret shown once.
    # Persist: key_prefix + bcrypt hash.
    from app.utils.api_keys import generate_api_key, validate_scopes

    name = (payload.get("name") or "New Key").strip()
    scopes = payload.get("scopes") or []

    validate_scopes(scopes)

    full_key, key_prefix, key_hash = generate_api_key()

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    key = APIKey(
        tenant_id=tenant_id,
        name=name,
        key_hash=key_hash,
        scopes=",".join(scopes),
        status="active",
    )

    session.add(key)
    await session.commit()
    await session.refresh(key)

    # Return secret once (create endpoint only)
    return {
        "api_key": full_key,
        "key": {
            "id": key.id,
            "tenant_id": tenant_id,
            "name": key.name,
            "key_prefix": key_prefix,
            "scopes": scopes,
            "active": True,


@router.patch("/{key_id}", response_model=APIKeyPublic)
async def toggle_api_key(
    key_id: str,
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    # Pydantic-style validation is handled by FastAPI; enforce boolean here for clear contract.
    if "active" not in payload or not isinstance(payload.get("active"), bool):
        # Let client see 422 consistent with body invalid.
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Invalid body: active must be boolean")

    desired_active: bool = payload["active"]

    # Fetch within tenant scope (avoid id leak)
    stmt = select(APIKey).where(APIKey.id == key_id, APIKey.tenant_id == tenant_id)
    key = (await session.execute(stmt)).scalars().first()
    if not key:
        raise AppError("NOT_FOUND", "API key not found", 404)

    meta = {
        "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
        "ip_address": getattr(request.state, "ip_address", None),
        "user_agent": getattr(request.state, "user_agent", None),
    }

    async def _audit_best_effort(*, action: str, result: str, status: str, details=None, error_code=None, error_message=None):
        try:
            await audit.log_event(
                session=session,
                request_id=meta["request_id"],
                actor_user_id=str(current_admin.id),
                actor_role=getattr(current_admin, "role", None),
                tenant_id=str(tenant_id),
                action=action,
                resource_type="api_key",
                resource_id=str(key.id),
                result=result,
                status=status,
                reason=request.headers.get("X-Reason"),
                ip_address=meta["ip_address"],
                user_agent=meta["user_agent"],
                details=details or {},
                error_code=error_code,
                error_message=error_message,
            )
        except Exception:
            try:
                await session.rollback()
            except Exception:
                pass

    before_active = key.status == "active"

    await _audit_best_effort(
        action="api_key.toggle.attempt",
        result="success",
        status="SUCCESS",
        details={"active_from": before_active, "active_to": desired_active},
    )

    try:
        key.status = "active" if desired_active else "inactive"
        # Schema does not currently include updated_at; keep deterministic anyway.
        # If later added, this can be set here.

        session.add(key)
        await session.commit()
        await session.refresh(key)

        await _audit_best_effort(
            action="api_key.toggled",
            result="success",
            status="SUCCESS",
            details={"active_from": before_active, "active_to": desired_active},
        )

        return APIKeyPublic(
            id=key.id,
            tenant_id=key.tenant_id,
            name=key.name,
            scopes=(key.scopes.split(",") if key.scopes else []),
            active=(key.status == "active"),
            created_at=key.created_at,
            last_used_at=None,
        )

    except Exception as exc:
        await _audit_best_effort(
            action="api_key.toggle.failed",
            result="failed",
            status="FAILED",
            error_code="API_KEY_TOGGLE_FAILED",
            error_message=str(exc),
            details={"active_from": before_active, "active_to": desired_active},
        )
        raise AppError("API_KEY_TOGGLE_FAILED", "Failed to toggle API key", 500)

            "created_at": key.created_at,
            "last_used_at": None,
        },
    }
