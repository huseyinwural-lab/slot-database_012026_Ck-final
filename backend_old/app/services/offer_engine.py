from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.offer_models import Offer, OfferDecisionRecord, Experiment
from app.models.sql_models import Player
from app.services.experiment_engine import ExperimentEngine

class OfferEngine:
    
    def __init__(self):
        self.exp_engine = ExperimentEngine()

    async def evaluate_trigger(self, session: AsyncSession, tenant_id: str, player_id: str, trigger_event: str, context: dict = None):
        """
        Main Entry Point: Decide what to offer based on trigger.
        Returns: OfferDecisionRecord
        """
        
        # 1. Load Context
        player = await session.get(Player, player_id)
        if not player:
            return None
            
        # 2. Check Policy Gates (RG, KYC, Risk)
        # MVP: Fail fast if RG excluded
        # (Assuming RG profile check logic is available or flags on Player)
        if player.status == "suspended" or "self_exclusion" in (player.risk_score or ""):
             return await self._log_decision(session, tenant_id, player_id, trigger_event, "denied", reason="RG_BLOCKED")

        # 3. Experiment Overlay
        # Is there an experiment for this trigger?
        # e.g. "welcome_offer_ab" for "first_deposit"
        exp_key = f"exp_{trigger_event}"
        variant = await self.exp_engine.get_assignment(session, tenant_id, player_id, exp_key)
        
        # 4. Select Offer based on Variant/Logic
        # Logic: If variant A -> Offer 1, Variant B -> Offer 2
        # MVP: Hardcoded mapping or lookup
        
        selected_offer_id = None
        
        if variant and variant != "control":
            # Find experiment to get config
            stmt = select(Experiment).where(Experiment.tenant_id == tenant_id, Experiment.key == exp_key)
            exp = (await session.execute(stmt)).scalars().first()
            if exp:
                variant_config = exp.variants.get(variant, {})
                selected_offer_id = variant_config.get("offer_id")
        
        # If no experiment or control, use Default Logic (Best Offer)
        if not selected_offer_id:
            # Simple Default: Find active offer matching trigger
            # (Requires Offer model to have 'trigger' field or similar. 
            #  For now, we query active offers and pick first valid)
            stmt_off = select(Offer).where(Offer.tenant_id == tenant_id, Offer.is_active == True)
            offers = (await session.execute(stmt_off)).scalars().all()
            if offers:
                selected_offer_id = offers[0].id # Naive pick
        
        if selected_offer_id:
            return await self._log_decision(session, tenant_id, player_id, trigger_event, "granted", offer_id=selected_offer_id, variant=variant)
        else:
            return await self._log_decision(session, tenant_id, player_id, trigger_event, "denied", reason="NO_OFFER_MATCH")

    async def _log_decision(self, session: AsyncSession, tenant_id: str, player_id: str, trigger: str, decision: str, offer_id: str = None, variant: str = None, reason: str = None):
        record = OfferDecisionRecord(
            tenant_id=tenant_id,
            player_id=player_id,
            trigger_event=trigger,
            decision=decision,
            offer_id=offer_id,
            variant=variant,
            deny_reason=reason
        )
        session.add(record)
        return record
