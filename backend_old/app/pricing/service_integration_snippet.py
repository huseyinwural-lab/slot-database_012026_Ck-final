from app.pricing.segment_resolver import SegmentPolicyResolver
from app.models import User

class PricingService:
    # ... existing init ...

    def calculate_quote(self, user_id: str, listing_type: str):
        # 1. Load User & Segment
        user = self.user_repo.get(user_id)
        segment = user.segment_type
        
        # 2. Resolve Policy
        policy = SegmentPolicyResolver.resolve(segment)
        
        # 3. Waterfall Core (Unchanged logic, updated limits)
        
        # Step A: Free Quota (Use Policy Limit)
        used_free = self.quota_service.get_usage(user_id, "FREE")
        if used_free < policy.free_quota:
            return Quote(price=0, type="FREE", duration=policy.listing_duration_days)
            
        # Step B: Package (Use Policy Access Check)
        if policy.package_access:
            if self.package_service.has_credits(user_id):
                return Quote(price=0, type="PACKAGE", duration=policy.listing_duration_days)
        
        # Step C: Paid (Use Policy Modifier)
        base_rate = self.rate_service.get_base_rate(listing_type)
        final_price = base_rate * policy.paid_rate_modifier
        
        return Quote(price=final_price, type="PAID", duration=policy.listing_duration_days)
