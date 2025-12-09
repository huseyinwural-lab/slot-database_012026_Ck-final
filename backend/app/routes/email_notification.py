from fastapi import APIRouter, HTTPException, status
from app.models.fraud import EmailNotificationRequest, EmailNotificationResponse
from app.services.sendgrid_service import email_service
import logging

router = APIRouter(prefix="/api/v1/email", tags=["email_notifications"])
logger = logging.getLogger(__name__)

@router.post("/send", response_model=EmailNotificationResponse)
async def send_email_notification(request: EmailNotificationRequest):
    try:
        result = email_service.send_email(
            recipient_email=request.recipient_email,
            subject=request.subject,
            html_content=request.body_html
        )
        return result
    except Exception as e:
        logger.error(f"Error in email endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
