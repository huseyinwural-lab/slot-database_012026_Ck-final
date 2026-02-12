# P1 Segment Policy Matrix

**Objective:** Map segments to specific pricing variables. This matrix drives the `PricingService`.

## 1. Policy Table

| Variable | INDIVIDUAL | DEALER |
| :--- | :--- | :--- |
| **Free Quota (Monthly)** | 3 Listings | 50 Listings |
| **Package Access** | ❌ NO | ✅ YES |
| **Pay-As-You-Go Rate** | Standard ($X) | Discounted ($Y) |
| **Listing Duration** | 30 Days | 60 Days |

## 2. Implementation Logic
- **Resolver:** `PolicyService.get_policy(segment: Segment) -> PolicyConfig`
- **Fallback:** If segment config is missing, raise Critical Error (Fail Closed).

## 3. Override Rules
- P1.1 does NOT support per-user overrides. The segment strictly dictates the policy.
