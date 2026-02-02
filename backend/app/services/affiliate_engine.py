from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.growth_models import Affiliate, AffiliateLink, AffiliateAttribution
from app.models.sql_models import LedgerTransaction
import uuid

class AffiliateEngine:
    async def attribute_player(self, session: AsyncSession, player_id: str, tenant_id: str, link_code: str):
        # 1. Resolve Link
        stmt = select(AffiliateLink).where(AffiliateLink.code == link_code, AffiliateLink.tenant_id == tenant_id)
        link = (await session.execute(stmt)).scalars().first()
        if not link:
            return None
            
        # 2. Create Attribution (Idempotent check needed in caller or unique constraint)
        # Using INSERT OR IGNORE logic in caller usually, here we assume check done
        attr = AffiliateAttribution(
            tenant_id=tenant_id,
            player_id=player_id,
            affiliate_id=link.affiliate_id,
            link_id=link.id
        )
        session.add(attr)
        
        # 3. Update Stats
        link.signups += 1
        session.add(link)
        
        return attr

    async def process_commission(self, session: AsyncSession, player_id: str, event_type: str, amount: float):
        # 1. Check Attribution
        stmt = select(AffiliateAttribution).where(AffiliateAttribution.player_id == player_id, AffiliateAttribution.status == 'active')
        attr = (await session.execute(stmt)).scalars().first()
        if not attr:
            return # No affiliate
            
        affiliate = await session.get(Affiliate, attr.affiliate_id)
        if not affiliate:
            return
            
        # 2. CPA Logic (First Deposit)
        commission = 0.0
        comm_type = ""
        
        if event_type == "FIRST_DEPOSIT" and affiliate.commission_type == "CPA":
            if amount >= affiliate.cpa_threshold:
                commission = affiliate.cpa_amount
                comm_type = "CPA"
                
        # 3. RevShare Logic (Bet/Loss) -> Not implemented fully in this snippet, assumes Deposit triggers for simplicity or NGR calc
        # For MVP Growth, let's stick to CPA on First Deposit
        
        if commission > 0:
            # Ledger Entry
            lt = LedgerTransaction(
                id=str(uuid.uuid4()),
                tenant_id=attr.tenant_id,
                player_id=affiliate.id, # Affiliate as 'player' in ledger or separate entity? 
                # Ideally separate, but for schema reuse we use player_id field for Entity ID
                type="affiliate_commission",
                amount=commission,
                currency="USD",
                status="accrued",
                direction="credit",
                provider="internal_affiliate",
                provider_ref=f"{comm_type}_{player_id}"
            )
            session.add(lt)
            return lt
        return None
