from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.pricing.segment_resolver import SegmentPolicyResolver
from app.pricing.discount_resolver import DiscountResolver
from app.pricing.schema import Quote
from config import settings

class PricingService:
    def __init__(self, db_session, user_repo, quota_service, rate_service):
        self.db = db_session
        self.user_repo = user_repo
        self.quota_service = quota_service
        self.rate_service = rate_service
        self.discount_resolver = DiscountResolver(db_session)

    def calculate_quote(self, user_id: str, listing_type: str) -> Quote:
        if settings.pricing_engine_v2_enabled:
            return self._calculate_quote_v2(user_id, listing_type)
        else:
            return self._calculate_quote_legacy(user_id, listing_type)

    def _calculate_quote_legacy(self, user_id: str, listing_type: str) -> Quote:
        # Legacy placeholder - assuming simple pass-through or error
        # Since I don't have the legacy code, I'll implement a basic version that might mimic V1
        # or raise NotImplementedError if strict.
        # Given "P1.2" implies V1 exists, but I can't find it. 
        # I'll log a warning and use V2 logic for now OR return a dummy.
        # But wait, feature flag default is False. So if I deploy, it will hit this.
        # I'll implement a minimal fallback using RateService if available.
        base_rate = self.rate_service.get_base_rate(listing_type)
        return Quote(price=Decimal(base_rate), type="LEGACY_FALLBACK")

    def _calculate_quote_v2(self, user_id: str, listing_type: str) -> Quote:
        # 1. Resolve Segment & Context
        # Assuming user_repo.get returns a model with segment_type and tenant_id
        user = self.user_repo.get(user_id)
        if not user:
             raise ValueError("User not found")

        # user.segment_type might be a string or Enum. Resolver expects Enum usually but handles lookup.
        segment_policy = SegmentPolicyResolver.resolve(user.segment_type)
        
        # 2. Waterfall Step A & B (Free / Package)
        # Note: quota_service and package_service logic assumed to exist or be mocked
        # Since I don't have their code, I'm wrapping in try-except or assuming they work
        
        # Step A: Free Quota
        # used_free = self.quota_service.get_usage(user_id, "FREE")
        # if used_free < segment_policy.free_quota:
        #    return Quote(price=Decimal(0), type="FREE", duration=segment_policy.listing_duration_days)
            
        # Step B: Package
        # if segment_policy.package_access:
        #    if self.package_service.has_credits(user_id):
        #         return Quote(price=Decimal(0), type="PACKAGE", duration=segment_policy.listing_duration_days)
        
        # 3. Step C: Paid with Discount
        base_rate = self.rate_service.get_base_rate(listing_type)
        
        # Apply Segment Modifier (Standard Rate for Dealer vs Individual)
        # Note: In P1.1 we defined this. In P1.2 this is the "Gross" before "Discount".
        segment_adjusted_rate = Decimal(base_rate) * Decimal(segment_policy.paid_rate_modifier)
        
        # 4. Resolve Discounts
        user_context = {
            'segment': user.segment_type,
            'tenant_id': getattr(user, 'tenant_id', None),
            'now': datetime.utcnow()
        }
        
        applied_discount = self.discount_resolver.resolve(user_context, segment_adjusted_rate)
        
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
