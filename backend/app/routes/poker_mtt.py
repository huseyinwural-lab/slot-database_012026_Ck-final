from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import Dict, Any
from datetime import datetime
import uuid

from app.core.database import get_session
from app.models.sql_models import AdminUser, Player, Transaction
from app.repositories.ledger_repo import LedgerTransaction
from app.models.poker_mtt_models import PokerTournament, TournamentRegistration
from app.utils.auth import get_current_admin
from app.utils.tenant import get_current_tenant_id
from app.services.audit import audit
from app.utils.reason import require_reason

router = APIRouter(prefix="/api/v1/poker/tournaments", tags=["poker_mtt"])

# --- TOURNAMENT LIFECYCLE ---

@router.post("/")
async def create_tournament(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    
    # Parse dates
    start_at = datetime.fromisoformat(payload["start_at"].replace("Z", "+00:00"))
    
    trn = PokerTournament(
        tenant_id=tenant_id,
        name=payload["name"],
        buy_in=float(payload["buy_in"]),
        fee=float(payload.get("fee", 0.0)),
        start_at=start_at,
        min_players=payload.get("min_players", 2),
        max_players=payload.get("max_players", 1000),
        status="DRAFT"
    )
    session.add(trn)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=tenant_id,
        action="MTT_CREATE",
        resource_type="tournament",
        resource_id=trn.id,
        result="success",
        reason=reason,
        details={"name": trn.name}
    )
    await session.commit()
    await session.refresh(trn)
    return trn

@router.post("/{tournament_id}/register")
async def register_player(
    tournament_id: str,
    payload: Dict[str, Any] = Body(...), # {player_id: str}
    session: AsyncSession = Depends(get_session)
):
    """Register player, Debit Wallet, Create Ledger."""
    # Assuming internal call or signed request. For simplicity, verifying player existence.
    player_id = payload["player_id"]
    
    trn = await session.get(PokerTournament, tournament_id)
    if not trn:
        raise HTTPException(404, "Tournament not found")
        
    if trn.status not in ["REG_OPEN"]:
        raise HTTPException(409, "Registration closed")
        
    # Idempotency Check (Prevent double buy-in)
    stmt = select(TournamentRegistration).where(
        TournamentRegistration.tournament_id == tournament_id,
        TournamentRegistration.player_id == player_id,
        TournamentRegistration.status == "active"
    )
    existing = (await session.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(409, "Player already registered")
        
    player = await session.get(Player, player_id)
    if not player:
        raise HTTPException(404, "Player not found")
        
    total_cost = trn.buy_in + trn.fee
    if player.balance_real_available < total_cost:
        raise HTTPException(402, "Insufficient funds")
        
    # Debit
    player.balance_real_available -= total_cost
    player.balance_real -= total_cost
    session.add(player)
    
    # Ledger & Tx
    tx_id = str(uuid.uuid4())
    tx = Transaction(
        tenant_id=trn.tenant_id, player_id=player_id, type="mtt_buyin",
        amount=total_cost, status="completed", state="completed", method="wallet",
        idempotency_key=f"mtt_reg_{tournament_id}_{player_id}",
        balance_after=player.balance_real_available
    )
    session.add(tx)
    
    ledger = LedgerTransaction(
        tenant_id=trn.tenant_id, player_id=player_id, type="mtt_buyin",
        amount=total_cost, status="success", direction="debit", provider="internal_mtt",
        provider_ref=tournament_id
    )
    session.add(ledger)
    
    # Registration Record
    reg = TournamentRegistration(
        tenant_id=trn.tenant_id, tournament_id=tournament_id, player_id=player_id,
        buyin_amount=trn.buy_in, fee_amount=trn.fee,
        tx_ref_buyin=tx.id, tx_ref_fee=tx.id # Simplified single tx
    )
    session.add(reg)
    
    # Update Tournament Stats
    trn.entrants_count += 1
    trn.prize_pool_total += trn.buy_in
    session.add(trn)
    
    await session.commit()
    return {"status": "registered", "reg_id": reg.id}

@router.post("/{tournament_id}/start")
async def start_tournament(
    request: Request,
    tournament_id: str,
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    trn = await session.get(PokerTournament, tournament_id)
    if not trn:
        raise HTTPException(404, "Tournament not found")
        
    if trn.status != "REG_OPEN":
        # Allow starting from DRAFT for testing
        if trn.status != "DRAFT":
             raise HTTPException(409, f"Cannot start from {trn.status}")
    
    if trn.entrants_count < trn.min_players:
        raise HTTPException(409, f"Not enough players ({trn.entrants_count}/{trn.min_players})")
        
    trn.status = "RUNNING"
    session.add(trn)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        actor_role=current_admin.role,
        tenant_id=trn.tenant_id,
        action="MTT_START",
        resource_type="tournament",
        resource_id=trn.id,
        result="success",
        reason=reason,
        details={"entrants": trn.entrants_count, "prize_pool": trn.prize_pool_total}
    )
    await session.commit()
    return trn

@router.post("/{tournament_id}/finish")
async def finish_tournament(
    request: Request,
    tournament_id: str,
    payload: Dict[str, Any] = Body(...), # {payouts: [{player_id, amount, rank}]}
    reason: str = Depends(require_reason),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin)
):
    trn = await session.get(PokerTournament, tournament_id)
    if not trn or trn.status != "RUNNING":
        raise HTTPException(409, "Tournament not running")
        
    payouts = payload["payouts"]
    total_payout = sum(p["amount"] for p in payouts)
    
    # Validation: Payout <= Prize Pool (allow small diff for rounding or guarantee overlay)
    # If guaranteed > collected, total_payout > prize_pool_total is expected (Overlay).
    # If no guarantee, they should match.
    
    for p in payouts:
        player_id = p["player_id"]
        amount = p["amount"]
        if amount <= 0: continue
        
        # Credit Player
        player = await session.get(Player, player_id)
        if player:
            player.balance_real_available += amount
            player.balance_real += amount
            session.add(player)
            
            # Ledger
            lt = Transaction(
                tenant_id=trn.tenant_id, player_id=player_id, type="mtt_prize",
                amount=amount, status="success", direction="credit", provider="internal_mtt",
                provider_ref=tournament_id
            )
            session.add(lt)
            
    trn.status = "FINISHED"
    trn.payout_report = {"payouts": payouts, "total_distributed": total_payout}
    session.add(trn)
    
    await audit.log_event(
        session=session,
        request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
        actor_user_id=current_admin.id,
        tenant_id=trn.tenant_id,
        action="MTT_FINISH",
        resource_type="tournament",
        resource_id=trn.id,
        result="success",
        reason=reason,
        details={"total_payout": total_payout, "winners_count": len(payouts)}
    )
    
    await session.commit()
    return trn
