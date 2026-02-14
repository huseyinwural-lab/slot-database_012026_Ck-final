from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from config import settings

from app.core.errors import AppError

from app.core.database import get_session
from sqlmodel import select
from datetime import datetime, timezone

from app.models.sql_models import AdminUser, CRMCampaign
from app.utils.auth import get_current_admin
from app.services.feature_access import enforce_module_access
from app.utils.tenant import get_current_tenant_id
from app.schemas.crm_email import CRMSendEmailRequest, CRMSendEmailResponse, CRMSendCampaignRequest
from app.services.resend_email import send_email


router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


# CRM minimal persistence for P0 Send

@router.get("/campaigns")
async def list_campaigns(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[dict]:
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")

    res = await session.execute(
        select(CRMCampaign).where(CRMCampaign.tenant_id == tenant_id).order_by(CRMCampaign.created_at.desc())
    )
    rows = res.scalars().all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "channel": c.channel,
            "status": c.status,
            "segment_id": c.segment_id,
            "template_id": c.template_id,
            "stats": {"sent": c.sent_count},
            "updated_at": c.updated_at.isoformat(),
        }
        for c in rows
    ]


@router.post("/campaigns")
async def create_campaign(
    request: Request,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")

    c = CRMCampaign(
        tenant_id=tenant_id,
        name=str(payload.get("name") or "Untitled"),
        channel=str(payload.get("channel") or "email"),
        segment_id=payload.get("segment_id"),
        template_id=payload.get("template_id"),
        status="draft",
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)

    return {
        "message": "CREATED",
        "campaign": {
            "id": c.id,
            "name": c.name,
            "channel": c.channel,
            "status": c.status,
            "segment_id": c.segment_id,
            "template_id": c.template_id,
            "stats": {"sent": c.sent_count},
            "updated_at": c.updated_at.isoformat(),
        },
    }


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    request: Request,
    body: CRMSendCampaignRequest | None = Body(default=None),
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")

    # Load campaign (must exist)
    res = await session.execute(
        select(CRMCampaign).where(CRMCampaign.id == campaign_id, CRMCampaign.tenant_id == tenant_id)
    )
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise AppError("CRM_CAMPAIGN_NOT_FOUND", "Campaign not found", 404)

    recipients = None
    subject = None
    html = None

    if body is not None:
        recipients = [str(x) for x in body.to]
        subject = body.subject
        html = body.html

    recipients = recipients or [settings.resend_test_to or settings.resend_reply_to or "huseyinwural@gmail.com"]
    subject = subject or f"CRM Campaign: {campaign.name}"
    html = html or f"<p>CRM campaign <strong>{campaign.name}</strong> sent.</p>"

    try:
        result = send_email(to=recipients, subject=subject, html=html)
        campaign.status = "completed"
        campaign.sent_count += len(recipients)
        campaign.last_error_code = None
    except AppError as e:
        campaign.status = "failed"
        campaign.last_error_code = e.error_code
        raise
    finally:
        campaign.updated_at = datetime.now(timezone.utc)
        session.add(campaign)
        await session.commit()

    return {"message": "SENT", "campaign_id": campaign_id, **result}


@router.post("/send-email", response_model=CRMSendEmailResponse)
async def crm_send_email(
    request: Request,
    payload: CRMSendEmailRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    """Minimal transactional email sender for CRM.

    P0 target: allow ad-hoc email sending via backend.
    """

    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")

    result = send_email(to=[str(x) for x in payload.to], subject=payload.subject, html=payload.html)
    return CRMSendEmailResponse(status="SENT", message_id=result["message_id"], provider=result["provider"])


@router.get("/templates")
async def list_templates(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[dict]:
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")
    return []


@router.get("/segments")
async def list_segments(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[dict]:
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")
    return []


@router.get("/channels")
async def list_channels(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[dict]:
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")
    return []


# Legacy root
@router.get("/")
async def get_crm(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[dict]:
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")
    return []
