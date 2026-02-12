# P1.2 Discount Cutover Plan

**Strategy:** Replace-in-Place with Feature Flag.

## 1. Feature Flag
`PRICING_ENGINE_V2_ENABLED` (default: `false` initially).

## 2. Code Changes
- **Refactor:** Move logic from `service_v2.py` into `PricingService`.
- **Toggle:**
  ```python
  if config.PRICING_ENGINE_V2_ENABLED:
      return self._calculate_quote_v2(user, listing_type)
  else:
      return self._calculate_quote_legacy(user, listing_type)
  ```

## 3. Deployment Steps
1. Deploy migration (Schema change).
2. Deploy code with flag `false`.
3. Verify basic functionality (Smoke Test).
4. Enable flag for QA Tenant.
5. Verify discount application.
6. Enable flag globally.
7. Remove legacy code path (P1.3).

## 4. Rollback
- Disable flag via environment variable reload.
