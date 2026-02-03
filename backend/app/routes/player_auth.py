import os
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from datetime import datetime, timezone, timedelta
from app.models.rg_models import PlayerRGProfile

from app.models.sql_models import Player, Tenant
from sqlalchemy.exc import IntegrityError
from app.services.affiliate_engine import AffiliateEngine
from app.core.database import get_session
from app.utils.auth import get_password_hash, verify_password, create_access_token
from app.schemas.player import PlayerPublic

router = APIRouter(prefix="/api/v1/auth/player", tags=["player_auth"])

@router.post("/register")
async def register_player(
    request: Request,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session),
):
    email = payload.get("email")
    tenant_id = payload.get("tenant_id", "default_casino")

    raw_limit = os.getenv("REGISTER_VELOCITY_LIMIT", "100")
    try:
        limit_count = int(raw_limit)
    except ValueError:
        limit_count = 100

    since = datetime.utcnow() - timedelta(minutes=1)
    current_count = (
        await session.execute(
            select(func.count())
            .select_from(Player)
            .where(Player.tenant_id == tenant_id)
            .where(Player.registered_at >= since)
        )
    ).scalar() or 0
    if current_count >= limit_count:
        raise HTTPException(status_code=429, detail="Too many registration requests")

    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        if tenant_id == "default_casino":
            tenant = Tenant(id="default_casino", name="Default Casino")
            session.add(tenant)
            await session.flush()
        else:
            raise HTTPException(status_code=400, detail="INVALID_TENANT")

    # Check exists
    stmt = select(Player).where(Player.email == email).where(Player.tenant_id == tenant_id)
    res = await session.execute(stmt)
    existing = res.scalars().first()
    if existing:
        raise HTTPException(400, "Player exists")
        
    password = payload.get("password")
    if not password or len(str(password)) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Hash password
    hashed_password = get_password_hash(password)
    
    player = Player(
        email=email,
        username=payload.get("username", email),
        tenant_id=tenant_id,
        password_hash=hashed_password,
        registered_at=datetime.utcnow(),
        last_login=None,
    )
    
    session.add(player)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="PLAYER_ALREADY_EXISTS")
    await session.refresh(player)  # Need ID for attribution

    player_id = str(player.id)

    # P0 Bonus: Onboarding auto-grant (best-effort)
    try:
        from app.services.bonus_lifecycle import auto_grant_onboarding_if_eligible

        await auto_grant_onboarding_if_eligible(session, tenant_id=tenant_id, player_id=player_id)
        await session.commit()
    except Exception:
        # no-op: onboarding may be missing or ambiguous; P0 spec allows no-op
        pass


    # Affiliate Attribution from referral cookie (P0)
    try:
        from app.services.affiliate_p0_engine import bind_attribution_on_register

        cookie_val = request.cookies.get("aff_ref") if request else None
        await bind_attribution_on_register(session, tenant_id=tenant_id, player_id=player_id, affiliate_code_cookie=cookie_val)
        await session.commit()
    except Exception:
        # best-effort; never break register
        pass

    # Affiliate Attribution
    referral_code = payload.get("referral_code") or payload.get("ref_code")
    if referral_code:
        aff_engine = AffiliateEngine()
        await aff_engine.attribute_player(session, player.id, tenant_id, referral_code)
        await session.commit()
    
    return {"message": "Registered", "player_id": player_id}

@router.post("/login")
async def login_player(payload: dict = Body(...), session: AsyncSession = Depends(get_session)):
    email = payload.get("email")
    tenant_id = payload.get("tenant_id", "default_casino")
    
    stmt = select(Player).where(Player.email == email).where(Player.tenant_id == tenant_id)
    res = await session.execute(stmt)
    player = res.scalars().first()
    
    if not player or not verify_password(payload.get("password"), player.password_hash):
        raise HTTPException(status_code=401, detail={"error_code": "INVALID_CREDENTIALS"})

    # P1-E1: suspended players cannot login
    if getattr(player, "status", None) == "suspended":
        raise HTTPException(status_code=403, detail={"error_code": "PLAYER_SUSPENDED"})

    # RG self-exclusion enforcement (deterministic): block login if player is self-excluded.
    stmt_rg = select(PlayerRGProfile).where(PlayerRGProfile.player_id == player.id)
    res_rg = await session.execute(stmt_rg)
    profile = res_rg.scalars().first()
    if profile:
        if bool(getattr(profile, "self_excluded_permanent", False)):
            raise HTTPException(status_code=403, detail="RG_SELF_EXCLUDED")
        until = getattr(profile, "self_excluded_until", None)
        if until and until > datetime.now(timezone.utc):
            raise HTTPException(status_code=403, detail="RG_SELF_EXCLUDED")

    token = create_access_token(
        data={"sub": player.id, "role": "player", "tenant_id": tenant_id},
        expires_delta=timedelta(days=7)
    )
    
    pub = PlayerPublic.model_validate(player)
    return {
        "access_token": token,
        "user": {
            "id": pub.id,
            "username": pub.username,
            "balance_real": pub.balance_real,
            "tenant_id": pub.tenant_id,
        }
    }
