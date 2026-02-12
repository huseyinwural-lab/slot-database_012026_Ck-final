# P1 Segment Integration Logic

**Target:** `PricingService.calculate_quote()`

## 1. Workflow Update

```python
def calculate_quote(user_id, listing_type):
    # 1. Resolve Segment
    user = user_repo.get(user_id)
    segment = user.segment_type  # Default INDIVIDUAL if strictly enforced schema

    # 2. Load Policy
    policy = policy_matrix.get(segment)

    # 3. Waterfall Execution (Order Preserved)
    
    # Step A: Free Quota
    if quota_service.has_remaining(user_id, policy.free_limit):
        return Quote(price=0, type="FREE")

    # Step B: Package (Dealer Only)
    if segment == "DEALER" and package_service.has_credits(user_id):
        return Quote(price=0, type="PACKAGE")

    # Step C: Paid
    base_price = base_rate_service.get(listing_type)
    final_price = apply_segment_rate(base_price, segment) # e.g. Dealer gets flat rate
    return Quote(price=final_price, type="PAID")
```

## 2. Impact Analysis
- **Low Risk:** Waterfall structure remains T2 compatible.
- **High Impact:** Users must have `segment_type` populated before this code deploys.
