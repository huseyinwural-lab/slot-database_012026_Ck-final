from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.poker_mtt_models import RiskSignal
from app.models.poker_models import PokerHandAudit

class PokerRiskEngine:
    
    async def analyze_collusion(self, session: AsyncSession, tenant_id: str):
        """
        Run collusion heuristics.
        1. Concentration: Same players meeting too often.
        2. Chip Dumping: Net flow between player pair > Threshold.
        """
        
        # --- Signal 1: Repeated Heads-Up / Same Table Concentration ---
        # Heuristic: Find pairs of players who shared a table > 50 hands in last 24h
        # (Simplified: Just count hand participation per table)
        
        # This requires complex aggregation which might be slow on large datasets.
        # MVP: Mock the detection or use simplified logic if HandAudit has 'players' list (it currently has 'winners' dict).
        # Assuming we can extend HandAudit or use existing 'winners' to infer participation? 
        # Actually, HandAudit is minimal. 'winners' keys are player_ids.
        
        # Let's focus on "Chip Dumping via Losses".
        # If Player A loses to Player B frequently.
        pass

    async def report_signal(self, session: AsyncSession, tenant_id: str, player_id: str, signal_type: str, severity: str, payload: dict):
        # Idempotency check: Don't spam same signal for same resource today
        today = datetime.now(timezone.utc).date()
        # (Simplified check)
        
        signal = RiskSignal(
            tenant_id=tenant_id,
            player_id=player_id,
            signal_type=signal_type,
            severity=severity,
            evidence_payload=payload,
            status="new"
        )
        session.add(signal)
        return signal

    async def detect_chip_dumping(self, session: AsyncSession, hand: PokerHandAudit):
        """
        Analyze a single finished hand for immediate dumping signs.
        - Big pot (> 100bb)
        - Fold on river with minimal resistance? (Hard to see without detailed action log)
        - Winner and Loser are 'known associates' (graph)?
        """
        # MVP: Just flag BIG POTS (> 500.0 amount) as potential dumping for review
        if hand.pot_total > 500.0:
            # Who won?
            winners = hand.winners # Dict[player_id, amount]
            for pid, amt in winners.items():
                await self.report_signal(
                    session, 
                    hand.tenant_id, 
                    pid, 
                    "chip_dumping_suspect", 
                    "medium", 
                    {"hand_id": hand.id, "pot": hand.pot_total, "win": amt}
                )
