from fastapi import APIRouter
from app.utils.auth import get_current_admin, AdminUser

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

@router.get("/")
async def get_settings():
    return {"theme": "default", "maintenance": False}
