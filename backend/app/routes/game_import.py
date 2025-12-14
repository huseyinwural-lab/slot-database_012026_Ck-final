from fastapi import APIRouter, Depends, Body
from app.utils.auth import get_current_admin, AdminUser

router = APIRouter(prefix="/api/v1/game-import", tags=["game_import"])

@router.post("/import")
async def import_games(
    provider: str = Body(...),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Mock Import Logic (SQL Compatible)
    return {"message": f"Import from {provider} queued"}
