from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_session
from app.models.sql_models import AdminUser
from app.utils.auth import get_current_admin
from app.services.feature_access import enforce_module_access
from app.utils.tenant import get_current_tenant_id
from app.schemas.crm_email import CRMSendEmailRequest, CRMSendEmailResponse
from app.services.resend_email import send_email


router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


# CRM stubs (UI contract)

@router.get("/campaigns")
async def list_campaigns(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
) -> List[dict]:
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")
    return []


@router.post("/campaigns")
async def create_campaign(
    request: Request,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")
    return {"message": "CREATED", "campaign": payload}


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_admin: AdminUser = Depends(get_current_admin),
):
    tenant_id = await get_current_tenant_id(request, current_admin, session=session)
    await enforce_module_access(session=session, tenant_id=tenant_id, module_key="crm")

    # P0: minimal email send (real inbox) using Resend.
    # Campaign storage/segments/templates are P2; here we send a deterministic placeholder email.
    result = send_email(
        to=os.environ.get("RESEND_TEST_TO") or os.environ.get("RESEND_REPLY_TO") or "huseyinwural@gmail.com",
        subject=f"CRM Campaign {campaign_id}",
        html=f"<p>CRM campaign <strong>{campaign_id}</strong> sent.</p>",
    )
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

    result = send_email(to=payload.to, subject=payload.subject, html=payload.html)
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
