from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timezone

from app.models.dispute_models import Dispute, AffiliateClawback
from app.models.sql_models import Transaction
from app.repositories.ledger_repo import append_event, apply_balance_delta

class DisputeEngine:
    
    async def create_dispute(self, session: AsyncSession, tenant_id: str, transaction_id: str, reason: str):
        # 1. Load Transaction
        tx = await session.get(Transaction, transaction_id)
        if not tx or tx.tenant_id != tenant_id:
            raise ValueError("Transaction not found")
            
        # 2. Check Existing
        stmt = select(Dispute).where(Dispute.transaction_id == transaction_id)
        existing = (await session.execute(stmt)).scalars().first()
        if existing:
            return existing
            
        # 3. Create Dispute Record
        dispute = Dispute(
            tenant_id=tenant_id,
            transaction_id=transaction_id,
            player_id=tx.player_id,
            amount=tx.amount,
            currency=tx.currency,
            reason_code=reason,
            status="OPEN"
        )
        session.add(dispute)
        
        # 4. Freeze Funds? 
        # Strategy: If player has balance, freeze it? Or just mark dispute?
        # For V1: Just mark dispute. If LOST, we deduct (reverse).
        
        return dispute

    async def resolve_dispute(self, session: AsyncSession, dispute_id: str, decision: str, note: str = None):
        """
        decision: WON (Merchant Wins - No Refund), LOST (Cardholder Wins - Chargeback)
        """
        dispute = await session.get(Dispute, dispute_id)
        if not dispute or dispute.status != "OPEN":
            raise ValueError("Dispute not actionable")
            
        dispute.status = decision
        dispute.resolved_at = datetime.now(timezone.utc)
        dispute.resolution_note = note
        session.add(dispute)
        
        if decision == "LOST":
            await self._process_chargeback(session, dispute)
            
        return dispute

    async def _process_chargeback(self, session: AsyncSession, dispute: Dispute):
        # 1. Reverse Transaction (Ledger Debit)
        # Assuming Deposit was Credit. Reversal is Debit.
        
        # Fee: Chargeback Fee? e.g. $15.00
        CB_FEE = 15.00
        
        # Debit Amount
        await append_event(
            session,
            tenant_id=dispute.tenant_id,
            player_id=dispute.player_id,
            tx_id=f"cb_{dispute.id}",
            type="chargeback",
            direction="debit",
            amount=dispute.amount,
            currency=dispute.currency,
            status="completed",
            provider="internal_dispute",
            provider_ref=dispute.id
        )
        
        # Debit Fee
        await append_event(
            session,
            tenant_id=dispute.tenant_id,
            player_id=dispute.player_id,
            tx_id=f"cb_fee_{dispute.id}",
            type="chargeback_fee",
            direction="debit",
            amount=CB_FEE,
            currency=dispute.currency,
            status="completed",
            provider="internal_dispute"
        )
        
        # Update Balance (can go negative)
        await apply_balance_delta(session, tenant_id=dispute.tenant_id, player_id=dispute.player_id, currency=dispute.currency, delta_available=-(dispute.amount + CB_FEE))
        
        # 2. Affiliate Clawback
        # Did this player sign up via affiliate?
        # Was commission paid?
        # Check Ledger for 'affiliate_commission' for this player/tx?
        # Simplification: If player has affiliate, deduct CPA/RevShare.
        
        from app.models.growth_models import AffiliateAttribution
        stmt = select(AffiliateAttribution).where(AffiliateAttribution.player_id == dispute.player_id)
        attr = (await session.execute(stmt)).scalars().first()
        
        if attr:
            # We assume CPA was paid. Reversal logic depends on commission model.
            # V1: Reverse a fixed "Standard CPA" or lookup original.
            # Lookup original commission tx?
            # Hard for MVP without link.
            # Let's deduct a "Clawback" amount = Dispute Amount * %? Or Full CPA?
            # Let's assume Full CPA Reversal if it was a First Deposit.
            # How do we know?
            # We log it as "Potential Clawback" for now.
            
            clawback_amount = 50.0 # Placeholder or lookup affiliate config
            
            ac = AffiliateClawback(
                tenant_id=dispute.tenant_id,
                affiliate_id=attr.affiliate_id,
                dispute_id=dispute.id,
                amount_reversed=clawback_amount
            )
            session.add(ac)
            
            # TODO: Debit Affiliate Ledger (if exists)
