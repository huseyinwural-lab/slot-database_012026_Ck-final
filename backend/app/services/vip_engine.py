from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime
import uuid

from app.models.vip_models import PlayerVipStatus, VipTier, LoyaltyTransaction
from app.models.sql_models import Player
from app.repositories.ledger_repo import append_event, apply_balance_delta

class VipEngine:
    
    async def get_status(self, session: AsyncSession, player_id: str, tenant_id: str) -> PlayerVipStatus:
        status = await session.get(PlayerVipStatus, player_id)
        if not status:
            status = PlayerVipStatus(player_id=player_id, tenant_id=tenant_id)
            session.add(status)
            await session.flush() # Ensure it exists for logic
        return status

    async def award_points(self, session: AsyncSession, player_id: str, tenant_id: str, points: float, source_type: str, source_ref: str):
        if points <= 0:
            return
            
        status = await self.get_status(session, player_id, tenant_id)
        
        # Update Balance
        status.lifetime_points += points
        status.current_points += points
        # DB uses TIMESTAMP WITHOUT TIME ZONE
        status.last_updated = datetime.utcnow()
        session.add(status)
        
        # Log Transaction
        tx = LoyaltyTransaction(
            tenant_id=tenant_id,
            player_id=player_id,
            type="ACCRUAL",
            amount=points,
            source_type=source_type,
            source_ref=source_ref,
            balance_after=status.current_points
        )
        session.add(tx)
        
        await self._check_tier_upgrade(session, status)
        
    async def redeem_points(self, session: AsyncSession, player_id: str, points_to_redeem: float, conversion_rate: float = 0.01):
        """
        Convert Points -> Cash.
        conversion_rate: $ per point. E.g. 0.01 means 100 points = $1.
        """
        status = await session.get(PlayerVipStatus, player_id)
        if not status or status.current_points < points_to_redeem:
            raise ValueError("Insufficient points")
            
        # 1. Deduct Points
        status.current_points -= points_to_redeem
        # DB uses TIMESTAMP WITHOUT TIME ZONE
        status.last_updated = datetime.utcnow()
        session.add(status)
        
        # 2. Log Loyalty Tx
        ltx = LoyaltyTransaction(
            tenant_id=status.tenant_id,
            player_id=player_id,
            type="REDEMPTION",
            amount=-points_to_redeem,
            source_type="CASH_CONVERSION",
            balance_after=status.current_points
        )
        session.add(ltx)
        
        # 3. Credit Wallet (Ledger)
        cash_amount = points_to_redeem * conversion_rate
        if cash_amount > 0:
            # Ledger Event
            await append_event(
                session,
                tenant_id=status.tenant_id,
                player_id=player_id,
                tx_id=ltx.id, # Use Loyalty Tx ID as reference
                type="adjustment",
                direction="credit",
                amount=cash_amount,
                currency="USD",
                status="completed",
                provider="internal_loyalty"
            )
            # Wallet Update
            await apply_balance_delta(
                session=session,
                tenant_id=status.tenant_id,
                player_id=player_id,
                currency="USD",
                delta_available=cash_amount
            )
            
        return cash_amount

    async def _check_tier_upgrade(self, session: AsyncSession, status: PlayerVipStatus):
        # Find highest eligible tier
        stmt = select(VipTier).where(
            VipTier.tenant_id == status.tenant_id, 
            VipTier.min_points <= status.lifetime_points
        ).order_by(VipTier.min_points.desc())
        
        best_tier = (await session.execute(stmt)).scalars().first()
        
        if best_tier and best_tier.id != status.current_tier_id:
            # Upgrade!
            status.current_tier_id = best_tier.id
            session.add(status)
            # TODO: Fire notification event
