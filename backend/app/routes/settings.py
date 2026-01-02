from fastapi import APIRouter, Depends
from app.utils.auth import get_current_admin, AdminUser

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

@router.get("/")
async def get_settings():
    return {"theme": "default", "maintenance": False}

@router.get("/brands")
async def get_brands(current_admin: AdminUser = Depends(get_current_admin)):
    # Minimal deterministic response for UI init / CI noise reduction.
    # Real implementation can be tenant-scoped brands catalog.
    return {
        "items": [
            {
                "id": "default_casino",
                "name": "Default Casino",
                "status": "active",
            }
        ]
    }

