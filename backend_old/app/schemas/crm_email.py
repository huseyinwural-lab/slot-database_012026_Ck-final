from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class CRMSendEmailRequest(BaseModel):
    to: List[EmailStr] = Field(min_length=1)
    subject: str = Field(min_length=1, max_length=200)
    html: str = Field(min_length=1)


class CRMSendEmailResponse(BaseModel):
    status: str
    message_id: str
    provider: str = "resend"


class CRMSendCampaignRequest(BaseModel):
    to: List[EmailStr] = Field(min_length=1)
    subject: Optional[str] = None
    html: Optional[str] = None
