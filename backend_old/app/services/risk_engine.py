from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta, timezone
from app.models.sql_models import Transaction, Player
from app.models.poker_mtt_models import RiskSignal

class RiskEngine:
    async def check_velocity(self, session: AsyncSession, player_id: str, tenant_id: str):
        """VEL-001: Check deposit velocity."""
        now = datetime.now(timezone.utc)
        window = now - timedelta(minutes=1)
        
        stmt = select(Transaction).where(
            Transaction.player_id == player_id,
            Transaction.type == 'deposit',
            Transaction.created_at > window
        )
        txs = (await session.execute(stmt)).scalars().all()
        
        if len(txs) > 5:
            # Trigger Signal
            sig = RiskSignal(
                tenant_id=tenant_id,
                player_id=player_id,
                signal_type="VEL-001",
                severity="medium",
                evidence_payload={"count": len(txs), "window": "1m"}
            )
            session.add(sig)
            # Update Player Risk Score
            player = await session.get(Player, player_id)
            if player:
                player.risk_score = "medium"
                session.add(player)
            return True
        return False
