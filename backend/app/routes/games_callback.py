from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Request, Body, Header
from sqlalchemy.ext.asyncio import AsyncSession
import time

from app.core.database import get_session
from app.services.game_engine import game_engine
from app.services.providers.registry import ProviderRegistry
from app.core.metrics import metrics
from app.core.errors import AppError

router = APIRouter(prefix="/api/v1/games/callback", tags=["games_callback"])

@router.post("/{provider}")
async def provider_callback(
    provider: str,
    request: Request,
    payload: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    start_time = time.time()
    try:
        # 1. Get Adapter
        try:
            adapter = ProviderRegistry.get_adapter(provider)
        except ValueError:
            raise HTTPException(status_code=404, detail="Provider not supported")

        # 2. Metrics (Request)
        action = payload.get("action", "unknown")
        metrics.provider_requests_total.labels(provider=provider, method=action, status="received").inc()

        # 3. Validate Signature
        # Note: Some providers use Headers, some use Body. Adapter handles it.
        # We pass raw payload usually, or request object. 
        # BaseProvider.validate_signature takes dict and headers.
        if not adapter.validate_signature(payload, dict(request.headers)):
            metrics.provider_signature_failures.labels(provider=provider).inc()
            raise HTTPException(status_code=403, detail="Invalid Signature")

        # 4. Map Request
        req_data = adapter.map_request(payload)
        cmd = req_data.get("action")
        
        result = {}
        
        # 5. Dispatch
        if cmd == "authenticate":
            token = req_data.get("token")
            player_id = await game_engine.authenticate(session, token)
            if not player_id:
                raise AppError("PLAYER_NOT_FOUND", "Invalid Token")
            # Return balance/profile
            result = await game_engine.get_balance(session, player_id, "USD")
            
        elif cmd == "balance":
            result = await game_engine.get_balance(
                session, 
                req_data.get("player_id"), 
                req_data.get("currency", "USD")
            )
            
        elif cmd == "bet":
            result = await game_engine.process_bet(
                session=session,
                provider=provider,
                provider_tx_id=req_data.get("tx_id"),
                player_id=req_data.get("player_id"),
                game_id=req_data.get("game_id"),
                round_id=req_data.get("round_id"),
                amount=req_data.get("amount"),
                currency=req_data.get("currency")
            )
            
        elif cmd == "win":
            result = await game_engine.process_win(
                session=session,
                provider=provider,
                provider_tx_id=req_data.get("tx_id"),
                player_id=req_data.get("player_id"),
                game_id=req_data.get("game_id"),
                round_id=req_data.get("round_id"),
                amount=req_data.get("amount"),
                currency=req_data.get("currency"),
                is_round_complete=True # Or extract from payload
            )
            
        elif cmd == "rollback":
            result = await game_engine.process_rollback(
                session=session,
                provider=provider,
                provider_tx_id=req_data.get("tx_id"),
                ref_provider_tx_id=req_data.get("ref_tx_id"),
                player_id=req_data.get("player_id"),
                game_id=req_data.get("game_id"),
                round_id=req_data.get("round_id"),
                amount=req_data.get("amount"),
                currency=req_data.get("currency")
            )
        else:
            raise AppError("INVALID_ACTION", f"Unknown action: {cmd}")

        await session.commit()
        
        # 6. Map Response
        response = adapter.map_response(result)
        metrics.provider_requests_total.labels(provider=provider, method=action, status="success").inc()
        return response

    except AppError as e:
        await session.rollback()
        metrics.provider_requests_total.labels(provider=provider, method=action, status="business_error").inc()
        # Map Error to Provider Format
        return adapter.map_error(e.error_code, e.message)
        
    except Exception as e:
        await session.rollback()
        metrics.provider_requests_total.labels(provider=provider, method=action, status="system_error").inc()
        # Default System Error
        return adapter.map_error("INTERNAL_ERROR", str(e))
    finally:
        # Latency metric if needed
        pass
