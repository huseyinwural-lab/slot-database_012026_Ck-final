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
        
        # P0: Deposit-triggered bonuses are out of scope for the new bonus engine.
        # Keep as a no-op to avoid conflicting bonus semantics.
        return
