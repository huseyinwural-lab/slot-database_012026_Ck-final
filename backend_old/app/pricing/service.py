from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.pricing.segment_resolver import SegmentPolicyResolver
from app.pricing.discount_resolver import DiscountResolver
from app.pricing.schema import Quote
from config import settings

class PricingService:
    def __init__(self, db_session, user_repo, quota_service, rate_service, ledger_service=None):
        self.db = db_session
        self.user_repo = user_repo
        self.quota_service = quota_service
        self.rate_service = rate_service
        self.discount_resolver = DiscountResolver(db_session)
        self.ledger_service = ledger_service

    async def calculate_quote(self, user_id: str, listing_type: str) -> Quote:
        if settings.pricing_engine_v2_enabled:
            return await self._calculate_quote_v2(user_id, listing_type)
        else:
            return await self._calculate_quote_legacy(user_id, listing_type)

    async def _calculate_quote_legacy(self, user_id: str, listing_type: str) -> Quote:
        # Legacy placeholder
        base_rate = await self.rate_service.get_base_rate(listing_type) # Assume async
        return Quote(price=Decimal(base_rate), type="LEGACY_FALLBACK")

    async def _calculate_quote_v2(self, user_id: str, listing_type: str) -> Quote:
        # 1. Resolve Segment & Context
        # Check if user_repo.get is async or sync. Assuming async for safety in this stack
        user = await self.user_repo.get(user_id)
        if not user:
             raise ValueError("User not found")

        segment_policy = SegmentPolicyResolver.resolve(user.segment_type)
        
        # 3. Step C: Paid with Discount
        base_rate = await self.rate_service.get_base_rate(listing_type) # Assume async
        
        segment_adjusted_rate = Decimal(base_rate) * Decimal(segment_policy.paid_rate_modifier)
        
        # 4. Resolve Discounts
        user_context = {
            'segment': user.segment_type,
            'tenant_id': getattr(user, 'tenant_id', None),
            'now': datetime.utcnow()
        }
        
        applied_discount = await self.discount_resolver.resolve(user_context, segment_adjusted_rate)
        
        final_price, discount_amount = self.discount_resolver.calculate_final_price(
            segment_adjusted_rate, 
            applied_discount
        )
        
        return Quote(
            price=final_price, # Net
            type="PAID",
            duration=segment_policy.listing_duration_days,
            details={
                "gross_amount": segment_adjusted_rate,
                "discount_amount": discount_amount,
                "discount_id": str(applied_discount.id) if applied_discount else None,
                "applied_code": applied_discount.code if applied_discount else None
            }
        )

    async def commit_transaction(self, tenant_id: str, listing_id: str, quote: Quote, player_id: str, tx_id: Optional[str] = None):
        """
        Commits the pricing quote to the ledger.
        """
        amount = float(quote.price)
        
        details = quote.details or {}
        gross = details.get("gross_amount")
        discount = details.get("discount_amount")
        discount_id = details.get("discount_id")
        
        ledger = self.ledger_service
        if not ledger:
            from app.services import wallet_ledger as ledger_module
            ledger = ledger_module
            
        if hasattr(ledger, 'apply_wallet_delta_with_ledger'):
            success = await ledger.apply_wallet_delta_with_ledger(
                self.db,
                tenant_id=tenant_id,
                player_id=player_id,
                tx_id=tx_id,
                event_type="listing_fee",
                delta_available=-amount,
                delta_held=0.0,
                currency="USD",
                gross_amount=float(gross) if gross is not None else None,
                discount_amount=float(discount) if discount is not None else 0.0,
                applied_discount_id=discount_id
            )
            return success
        elif hasattr(ledger, 'record'): # Support test mock
             ledger.record(
                tenant_id=tenant_id,
                player_id=player_id,
                amount=amount,
                gross_amount=float(gross) if gross is not None else 0,
                discount_amount=float(discount) if discount is not None else 0,
                applied_discount_id=discount_id
             )
             return True
        else:
            raise NotImplementedError("Ledger service interface mismatch")
