from app.pricing.segment_resolver import SegmentPolicyResolver
from app.pricing.discount_resolver import DiscountResolver
from datetime import datetime
from decimal import Decimal

class PricingService:
    def __init__(self, db_session, user_repo, quota_service, rate_service):
        self.db = db_session
        self.user_repo = user_repo
        self.quota_service = quota_service
        self.rate_service = rate_service
        self.discount_resolver = DiscountResolver(db_session)

    def calculate_quote(self, user_id: str, listing_type: str):
        # 1. Resolve Segment & Context
        user = self.user_repo.get(user_id)
        segment_policy = SegmentPolicyResolver.resolve(user.segment_type)
        
        # 2. Waterfall Step A & B (Free / Package)
        # ... existing logic ...
        # if free quota available -> return Quote(0, "FREE")
        
        # 3. Step C: Paid with Discount
        base_rate = self.rate_service.get_base_rate(listing_type)
        
        # Apply Segment Modifier (Standard Rate for Dealer vs Individual)
        # Note: In P1.1 we defined this. In P1.2 this is the "Gross" before "Discount".
        segment_adjusted_rate = base_rate * segment_policy.paid_rate_modifier
        
        # 4. Resolve Discounts
        user_context = {
            'segment': user.segment_type,
            'tenant_id': user.tenant_id,
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
            details={
                "gross_amount": segment_adjusted_rate,
                "discount_amount": discount_amount,
                "discount_id": applied_discount.id if applied_discount else None,
                "applied_code": applied_discount.code if applied_discount else None
            }
        )
