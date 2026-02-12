# P1 Discount Abuse Model

**Threats & Mitigations**

## 1. Cycle Abuse (Segment Hopping)
- **Threat:** User switches to DEALER to get discount, then switches back.
- **Mitigation:** Segment transition rate limit (already in P1.1). Discount valid only while in segment.

## 2. Stacking Exploit
- **Threat:** User applies "Summer Sale" + "Dealer Discount" + "Apology Coupon".
- **Mitigation:** Strict "No Stacking" policy enforced by Resolver. Only highest priority rule applies.

## 3. Expired Discount
- **Threat:** User gets quote, waits for discount to expire, then commits.
- **Mitigation:** Quote validity period (e.g., 15 mins). Re-validate discount active status at `commit` time.

## 4. Negative Price
- **Threat:** Flat discount > Base price.
- **Mitigation:** `max(0, calculated_price)` clamp logic.
