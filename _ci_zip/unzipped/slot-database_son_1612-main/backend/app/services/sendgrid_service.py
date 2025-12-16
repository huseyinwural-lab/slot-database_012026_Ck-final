from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To
from config import settings
from app.models.fraud import EmailNotificationResponse
import logging

logger = logging.getLogger(__name__)

class SendGridEmailService:
    def __init__(self):
        self.sg_client = SendGridAPIClient(settings.sendgrid_api_key) if settings.sendgrid_api_key else None
        self.from_email = Email(settings.sendgrid_from_email)
    
    def send_email(self, recipient_email: str, subject: str, html_content: str) -> EmailNotificationResponse:
        if not self.sg_client:
             return EmailNotificationResponse(
                email_id="mock-id",
                recipient=recipient_email,
                status="sent",
                error_message="Mock Mode: No API Key"
            )

        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=To(recipient_email),
                subject=subject,
                html_content=html_content
            )
            response = self.sg_client.send(message)
            
            if response.status_code == 202:
                return EmailNotificationResponse(
                    email_id=response.headers.get('X-Message-ID', 'unknown'),
                    recipient=recipient_email,
                    status="sent"
                )
            else:
                 return EmailNotificationResponse(
                    email_id="",
                    recipient=recipient_email,
                    status="failed",
                    error_message=f"Status: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"SendGrid Error: {str(e)}")
            return EmailNotificationResponse(
                email_id="",
                recipient=recipient_email,
                status="failed",
                error_message=str(e)
            )

email_service = SendGridEmailService()
