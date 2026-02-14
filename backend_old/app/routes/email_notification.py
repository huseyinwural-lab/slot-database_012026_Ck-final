from fastapi import APIRouter, Depends, Body
from app.utils.auth import get_current_admin, AdminUser

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.post("/send")
async def send_notification(
    payload: dict = Body(...),
    current_admin: AdminUser = Depends(get_current_admin)
):
    # Mock Notification Logic
    return {"message": "Notification sent"}
