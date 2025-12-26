from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.game_schemas import ProviderEvent, ProviderResponse
from app.services.game_engine import GameEngine
from app.core.errors import AppError
import logging

router = APIRouter(prefix="/api/v1/integrations", tags=["game_integrations"])
logger = logging.getLogger(__name__)

@router.post("/callback", response_model=ProviderResponse)
async def provider_callback(
    payload: ProviderEvent,
    session: AsyncSession = Depends(get_session)
):
from app.middleware.callback_security import verify_signature
    """
    Unified Callback Endpoint for Game Providers.
    Accepts BET/WIN/REFUND events.
    """
    security_check: bool = Depends(verify_signature)
    try:
        # TODO: Verify Signature here using payload.signature and provider secret
        # For mock, we skip validation or assume it's valid
        
        response = await GameEngine.process_event(session, payload)
        return response
    except AppError as e:
        logger.error(f"Game Logic Error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Callback Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
