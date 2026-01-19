from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
import uuid


from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import (
    DashboardStats, KPIMetric
)
from app.models.sql_models import (
    Player, Transaction, AdminUser
)
from app.models.game_models import Game
from app.schemas.player import PlayerPublic
from app.utils.tenant import get_current_tenant_id
from app.utils.auth import get_current_admin
from app.utils.pagination import get_pagination_params
from app.models.common import PaginationMeta, PaginationParams
from app.schemas.pagination import PaginatedResponsePublic
from app.core.database import get_session
from app.utils.permissions import require_support_view

from app.core.errors import AppError


# Router
router = APIRouter(prefix="/api/v1", tags=["core"])

# --- DASHBOARD ---
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_session)
):
    # Total Bets (Sum of 'bet' transactions)
    bets_query = select(func.sum(Transaction.amount)).where(Transaction.type == "bet")
    bets_result = await session.execute(bets_query)
    bets_today = bets_result.scalar() or 0.0

    # Total Wins
    wins_query = select(func.sum(Transaction.amount)).where(Transaction.type == "win")
    wins_result = await session.execute(wins_query)
    wins_today = wins_result.scalar() or 0.0

    ggr_today = bets_today - wins_today
    bonuses_today = 0.0 
    ngr_today = ggr_today - bonuses_today - (ggr_today * 0.15)
    
    # Counts
    pending_wit = (await session.execute(select(func.count()).select_from(Transaction).where(Transaction.type == "withdrawal", Transaction.status == "pending"))).scalar() or 0
    pending_kyc = (await session.execute(select(func.count()).select_from(Player).where(Player.kyc_status == "pending"))).scalar() or 0
    
    # Recent Players (placeholder - future use)
    _recent_players = (await session.execute(select(Player).order_by(Player.registered_at.desc()).limit(5))).scalars().all()

    return DashboardStats(
        ggr=KPIMetric(value=ggr_today, change_percent=0.0, trend="up"),
        ngr=KPIMetric(value=ngr_today, change_percent=0.0, trend="up"),
        total_bets=KPIMetric(value=bets_today, change_percent=0.0, trend="up"),
        total_wins=KPIMetric(value=wins_today, change_percent=0.0, trend="up"),
        provider_health=[{"name": "Pragmatic", "status": "UP"}],
        payment_health=[{"name": "Papara", "status": "UP"}],
        risk_alerts={"high_risk_withdrawals": 0, "vpn_detected": 0},
        online_users=0, 
        active_sessions=0, 
        peak_sessions_24h=0,
        bonuses_given_today_count=0, 
        bonuses_given_today_amount=0.0,
        top_games=[],
        recent_registrations=[], 
        pending_withdrawals_count=pending_wit, 
        pending_kyc_count=pending_kyc
    )


@router.post("/players", status_code=201)
async def create_player_admin(
    request: Request,
    payload: dict = Body(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Admin create player (P1BS-G1-001).

    Contract:
    - Path: POST /api/v1/players
    - Tenant boundary: created in caller tenant only
    - Password required
    - Response includes player_id
    """

    # RBAC: require admin role
    if getattr(current_admin, "role", None) != "Admin":
        raise HTTPException(status_code=403, detail={"error_code": "FORBIDDEN"})

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    username = payload.get("username")
    password = payload.get("password")
    email = payload.get("email") or f"{username}@example.com" if username else None

    if not username:
        raise HTTPException(status_code=400, detail={"error_code": "USERNAME_REQUIRED"})
    if not password:
        raise HTTPException(status_code=400, detail={"error_code": "PASSWORD_REQUIRED"})

    # Uniqueness (tenant scope)
    existing = (
        await session.execute(select(Player).where(Player.tenant_id == tenant_id, Player.username == username))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=409, detail={"error_code": "USERNAME_EXISTS"})

    if email:
        existing_email = (
            await session.execute(select(Player).where(Player.tenant_id == tenant_id, Player.email == email))
        ).scalars().first()
        if existing_email:
            raise HTTPException(status_code=409, detail={"error_code": "EMAIL_EXISTS"})

    from app.utils.auth import get_password_hash

    player = Player(
        tenant_id=tenant_id,
        username=username,
        email=email or "",
        password_hash=get_password_hash(password),
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)

    # Audit (best-effort)
    try:
        from app.services.audit import audit

        request_id = request.headers.get("X-Request-Id", "unknown")
        await audit.log(
            admin=current_admin,
            action="player.create",
            module="player",
            target_id=player.id,
            details={"username": username, "email": email},
            session=session,
            request_id=request_id,
            tenant_id=tenant_id,
            resource_type="player",
            result="success",
        )
        await session.commit()
    except Exception:
        pass

    return {
        "player_id": player.id,
        "username": player.username,
        "status": player.status,
    }

# --- PLAYERS ---
@router.get("/players", response_model=PaginatedResponsePublic[PlayerPublic])
async def get_players(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    include_disabled: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    require_support_view(current_admin)
    query = select(Player)
    
    # Tenant Filter (P0-TENANT-SCOPE)
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = query.where(Player.tenant_id == tenant_id)
    
    # Status has precedence over include_disabled.
    if status and status != "all":
        query = query.where(Player.status == status)
    else:
        # Default: hide disabled players unless include_disabled is truthy.
        truthy = {"1", "true", "yes"}
        include = (include_disabled or "").strip().lower() in truthy
        if not include:
            query = query.where(Player.status != "disabled")
        
    if search:
        query = query.where(
            (Player.username.ilike(f"%{search}%")) | 
            (Player.email.ilike(f"%{search}%"))
        )

    query = query.order_by(Player.registered_at.desc())

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    result = await session.execute(query)
    players = result.scalars().all()

    return {
        "items": [PlayerPublic.model_validate(p) for p in players],
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size),
    }


@router.get("/players/export")
async def export_players_csv(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Export players as CSV.

    MVP: deterministic columns that match UI list where available.
    Tenant scoped (owner impersonation via X-Tenant-ID).
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    query = select(Player).where(Player.tenant_id == tenant_id)

    if status and status != "all":
        query = query.where(Player.status == status)

    if search:
        query = query.where((Player.username.ilike(f"%{search}%")) | (Player.email.ilike(f"%{search}%")))

    query = query.order_by(Player.registered_at.desc()).limit(5000)
    result = await session.execute(query)
    players = result.scalars().all()

    rows = []
    for p in players:
        rows.append(
            {
                "id": p.id,
                "username": p.username,
                "email": p.email,
                "status": p.status,
                "kyc_status": p.kyc_status,
                "risk_score": p.risk_score,
                "balance_real": p.balance_real,
                "balance_bonus": p.balance_bonus,
                "registered_at": p.registered_at.isoformat() if getattr(p, "registered_at", None) else "",
            }
        )

    from app.services.csv_export import dicts_to_csv_bytes

    csv_bytes = dicts_to_csv_bytes(
        rows,
        fieldnames=[
            "id",
            "username",
            "email",
            "status",
            "kyc_status",
            "risk_score",
            "balance_real",
            "balance_bonus",
            "registered_at",
        ],
    )

    filename = (
        f"players_{tenant_id}_{request.state.request_id}.csv"
        if getattr(request.state, "request_id", None)
        else f"players_{tenant_id}.csv"
    )

    from fastapi.responses import Response

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )




@router.get("/players/export.xlsx")
async def export_players_xlsx(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    vip_level: Optional[str] = None,
    risk_score: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Export players as XLSX (Excel).

    Keeps CSV endpoint for backward compatibility.
    Tenant scoped (owner impersonation via X-Tenant-ID).
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    query = select(Player).where(Player.tenant_id == tenant_id)

    if status and status != "all":
        query = query.where(Player.status == status)

    # vip_level is not currently stored on Player model in this repo.
    # Keep param accepted for UI compatibility but do not filter.

    if risk_score and risk_score != "all":
        query = query.where(Player.risk_score == risk_score)

    if search:
        query = query.where((Player.username.ilike(f"%{search}%")) | (Player.email.ilike(f"%{search}%")))

    query = query.order_by(Player.registered_at.desc()).limit(5000)
    result = await session.execute(query)
    players = result.scalars().all()

    rows = []
    for p in players:
        rows.append(
            {
                "id": p.id,
                "username": p.username,
                "email": p.email,
                "status": p.status,
                "kyc_status": p.kyc_status,
                "vip_level": "",
                "risk_score": p.risk_score,
                "balance_real": p.balance_real,
                "balance_bonus": p.balance_bonus,
                "registered_at": p.registered_at.isoformat() if getattr(p, "registered_at", None) else "",
            }
        )

    from app.services.xlsx_export import dicts_to_xlsx_bytes

    columns = [
        "id",
        "username",
        "email",
        "status",
        "kyc_status",
        "vip_level",
        "risk_score",
        "balance_real",
        "balance_bonus",
        "registered_at",
    ]

    xlsx_bytes = dicts_to_xlsx_bytes(rows, columns=columns)

    filename = (
        f"players_{tenant_id}_{request.state.request_id}.xlsx"
        if getattr(request.state, "request_id", None)
        else f"players_{tenant_id}.xlsx"
    )

    from fastapi.responses import Response

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )

@router.get("/players/{player_id}", response_model=PlayerPublic)
async def get_player_detail(
    player_id: str,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Player).where(Player.id == player_id, Player.tenant_id == tenant_id)
    res = await session.execute(stmt)
    player = res.scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return PlayerPublic.model_validate(player)

@router.put("/players/{player_id}")
async def update_player(
    player_id: str,
    request: Request,
    update_data: Dict = Body(...),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Player).where(Player.id == player_id, Player.tenant_id == tenant_id)
    res = await session.execute(stmt)
    player = res.scalars().first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    for k, v in update_data.items():
        if hasattr(player, k):
            setattr(player, k, v)

    session.add(player)
    await session.commit()
    return {"message": "Player updated"}



# --- FINANCE ---
@router.get("/finance/transactions", response_model=dict)
async def get_transactions(
    request: Request,
    type: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    query = select(Transaction)
    
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = query.where(Transaction.tenant_id == tenant_id)
        
    if type and type != "all":
        query = query.where(Transaction.type == type)
    if status and status != "all":
        query = query.where(Transaction.status == status)
        
    query = query.order_by(Transaction.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    result = await session.execute(query)
    txs = result.scalars().all()
    
    return {
        "items": txs,
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size),
    }

# --- GAMES ---
# NOTE: This endpoint uses PaginatedResponse format. Frontend must match this.
@router.get("/games", response_model=dict) # Changing to dict to be safe with structure
async def get_games(
    request: Request,
    category: Optional[str] = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    query = select(Game)
    
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    query = query.where(Game.tenant_id == tenant_id)
        
    if category and category != "all":
        query = query.where(Game.category == category)
        
    query = query.order_by(Game.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0
    
    query = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)
    result = await session.execute(query)
    games = result.scalars().all()
    
    # Frontend likely expects ARRAY for games list based on VipGames.jsx: const all = res.data;
    # But GameManagement.jsx might expect pagination.
    # Let's check common usage. 
    # VipGames.jsx does: const res = await api.get('/v1/games'); const all = res.data;
    # This implies it expects an ARRAY directly, NOT { items: [...] }.
    # BUT GameManagement.jsx likely uses table with pagination.
    
    # Conflict: VipGames expects Array, GameManagement expects Paginated.
    # SOLUTION: Return array if pagination not requested or handle both.
    # OR better: Standardize Frontend to always read .items if present.
    # Since I cannot easily change all Frontend files in one shot without risk, 
    # I will modify this endpoint to return ARRAY if page_size is large (mocking "all") 
    # OR check if we can return a structure that satisfies both (impossible).
    
    # Let's return the standard { items: [], meta: {} } 
    # AND I will patch VipGames.jsx to read .items if it exists.
    
    items = []
    for g in games:
        active = bool(getattr(g, "is_active", False))
        cfg = g.configuration if isinstance(getattr(g, "configuration", None), dict) else {}
        items.append(
            {
                **g.model_dump(),
                "tags": cfg.get("tags", []),
                "business_status": "active" if active else "inactive",
                "runtime_status": "online" if active else "offline",
            }
        )

    return {
        "items": items,
        "meta": PaginationMeta(total=total, page=pagination.page, page_size=pagination.page_size),
    }


@router.post("/games/{game_id}/toggle", response_model=dict)
async def toggle_game_active(
    game_id: str,
    request: Request,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Toggle game active state.

    Semantics:
    - `is_active=true` => active/online
    - `is_active=false` => inactive/offline
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Game).where(Game.id == game_id, Game.tenant_id == tenant_id)
    res = await session.execute(stmt)
    game = res.scalars().first()
    if not game:
        raise AppError(
            error_code="GAME_NOT_FOUND",
            message="Game not found",
            status_code=404,
            details={"game_id": game_id},
        )

    game.is_active = not bool(getattr(game, "is_active", False))
    session.add(game)
    await session.commit()
    await session.refresh(game)

    return {
        "id": game.id,
        "is_active": game.is_active,
        "business_status": "active" if game.is_active else "inactive",
        "runtime_status": "online" if game.is_active else "offline",
    }


@router.put("/games/{game_id}/details", response_model=dict)
async def update_game_details(
    game_id: str,
    payload: Dict[str, Any] = Body(...),
    request: Request = None,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
):
    """Update game metadata used by admin UIs.

    Currently supported fields:
    - tags: List[str]

    Notes:
    - We store tags inside `Game.configuration["tags"]` to avoid DB migrations.
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)

    stmt = select(Game).where(Game.id == game_id, Game.tenant_id == tenant_id)
    res = await session.execute(stmt)
    game = res.scalars().first()
    if not game:
        raise AppError(
            error_code="GAME_NOT_FOUND",
            message="Game not found",
            status_code=404,
            details={"game_id": game_id},
        )

    tags = payload.get("tags")
    if tags is None:
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_FAILED", "message": "tags required"})
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_FAILED", "message": "tags must be list[str]"})

    cfg = game.configuration if isinstance(game.configuration, dict) else {}
    # Important: assign a NEW dict so JSON change is persisted (JSON column is not mutable-tracked).
    game.configuration = {**cfg, "tags": tags}

    session.add(game)
    await session.commit()
    await session.refresh(game)

    return {
        "id": game.id,
        "tags": tags,
    }

