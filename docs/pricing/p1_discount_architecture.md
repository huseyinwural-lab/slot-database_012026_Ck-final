# P1 Discount Architecture

**Flow:** Serial Resolver Chain.

```mermaid
graph TD
    A[PricingService.calculate_quote()] --> B[SegmentPolicyResolver]
    B --> C{Allocation Logic}
    C -- Free/Package --> D[Final Quote (0.00)]
    C -- Paid --> E[DiscountPolicyResolver]
    E --> F[Fetch Active Rules]
    F --> G[Apply Top Priority Rule]
    G --> H[Final Quote (Net Price)]
```

## Responsibilities
- **PricingService:** Orchestrator.
- **SegmentPolicyResolver:** Determines Base Rate & Limits.
- **DiscountPolicyResolver:** Determines Net Price Modifier.

## Interface
```python
class DiscountResolver:
    def resolve(self, user_context, base_price):
        # 1. Fetch Rules
        # 2. Filter Active
        # 3. Apply Priority
        # 4. Return DiscountApplied object (amount, reason)
```
