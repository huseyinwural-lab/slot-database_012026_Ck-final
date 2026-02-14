from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.game_schemas import ProviderEvent, ProviderResponse
from app.services.game_engine import GameEngine
from app.core.errors import AppError
from app.middleware.callback_security import verify_signature
import logging

router = APIRouter(prefix="/api/v1/integrations", tags=["game_integrations"])
logger = logging.getLogger(__name__)

@router.post("/callback", response_model=ProviderResponse)
async def provider_callback(
    payload: ProviderEvent,
    session: AsyncSession = Depends(get_session),
    _ = Depends(verify_signature)
):
    """
    Unified Callback Endpoint for Game Providers.
    Accepts BET/WIN/REFUND events.
    """
    try:
        response = await GameEngine.process_event(session, payload)
        return response
    except AppError as e:
        logger.error(f"Game Logic Error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Callback Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
