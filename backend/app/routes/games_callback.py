from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Request, Body, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.game_engine import game_engine
from app.models.sql_models import Player
from app.core.errors import AppError
from sqlalchemy.future import select

router = APIRouter(prefix="/api/v1/games/callback", tags=["games_callback"])

@router.post("/{provider}")
async def provider_callback(
    provider: str,
    request: Request,
    payload: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """Generic Provider Callback Router.
    
    In a real implementation, we would have a 'ProviderRegistry' to load
    specific adapters (PragmaticAdapter, EvolutionAdapter).
    For Phase 3, we implement the 'Simulator' logic directly here or via a simple helper.
    """
    
    if provider != "simulator":
        raise HTTPException(status_code=404, detail="Provider not supported")

    # Simulator Payload Structure:
    # {
    #   "action": "bet" | "win" | "rollback",
    #   "player_id": "...",
    #   "game_id": "...",
    #   "round_id": "...",
    #   "tx_id": "...",
    #   "amount": 10.0,
    #   "currency": "USD",
    #   "ref_tx_id": "..." (for rollback)
    # }

    action = payload.get("action")
    player_id = payload.get("player_id")
    game_id = payload.get("game_id")
    round_id = payload.get("round_id")
    tx_id = payload.get("tx_id")
    amount = float(payload.get("amount", 0.0))
    currency = payload.get("currency", "USD")

    # Validate Player
    stmt = select(Player).where(Player.id == player_id)
    player = (await session.execute(stmt)).scalars().first()
    if not player:
        raise HTTPException(status_code=400, detail="Player not found")

    try:
        if action == "bet":
            result = await game_engine.process_bet(
                session=session,
                provider=provider,
                provider_tx_id=tx_id,
                player_id=player_id,
                game_id=game_id,
                round_id=round_id,
                amount=amount,
                currency=currency
            )
        elif action == "win":
            result = await game_engine.process_win(
                session=session,
                provider=provider,
                provider_tx_id=tx_id,
                player_id=player_id,
                game_id=game_id,
                round_id=round_id,
                amount=amount,
                currency=currency,
                is_round_complete=True
            )
        elif action == "rollback":
            ref_tx_id = payload.get("ref_tx_id")
            result = await game_engine.process_rollback(
                session=session,
                provider=provider,
                provider_tx_id=tx_id,
                ref_provider_tx_id=ref_tx_id,
                player_id=player_id,
                game_id=game_id,
                round_id=round_id,
                amount=amount,
                currency=currency
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
            
        await session.commit()
        return {"status": "OK", "data": result}

    except AppError as e:
        await session.rollback()
        # Map Engine errors to HTTP responses
        if e.error_code == "INSUFFICIENT_FUNDS":
            raise HTTPException(status_code=402, detail="INSUFFICIENT_FUNDS")
        elif e.error_code == "GAME_NOT_FOUND":
            raise HTTPException(status_code=404, detail="GAME_NOT_FOUND")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
