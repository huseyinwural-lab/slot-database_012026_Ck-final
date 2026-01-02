from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.growth_models import GrowthEvent
from app.models.bonus_models import BonusCampaign, BonusGrant
from app.models.sql_models import Player
from app.services.audit import audit
from datetime import datetime, timedelta
import uuid

class CRMEngine:
    async def process_event(self, session: AsyncSession, event: GrowthEvent):
        # 1. Match Triggers (Hardcoded MVP)
        if event.event_type == "FIRST_DEPOSIT":
            await self.trigger_welcome_bonus(session, event)
            
        event.processed = True
        session.add(event)
        
    async def trigger_welcome_bonus(self, session: AsyncSession, event: GrowthEvent):
        tenant_id = event.tenant_id
        player_id = event.player_id
        
        # Check eligibility (Simple: No active bonus)
        # Load active campaigns
        stmt = select(BonusCampaign).where(BonusCampaign.tenant_id == tenant_id, BonusCampaign.status == 'active', BonusCampaign.type == 'deposit_match')
        campaign = (await session.execute(stmt)).scalars().first()
        
        if campaign:
            # Grant
            # Use logic from Bonus Route/Service (duplicated here for simplicity/speed)
            grant = BonusGrant(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                campaign_id=campaign.id,
                player_id=player_id,
                amount_granted=50.0, # Mock fixed amount or based on payload
                initial_balance=50.0,
                wagering_target=50.0 * 35,
                status="active",
                granted_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            session.add(grant)
            
            # Audit
            await audit.log_event(
                session=session,
                request_id=f"crm_{event.id}",
                actor_user_id="system-crm",
                tenant_id=tenant_id,
                action="CRM_OFFER_GRANT",
                resource_type="bonus_grant",
                resource_id=grant.id,
                result="success",
                reason="First Deposit Trigger",
                details={"campaign": campaign.name}
            )
