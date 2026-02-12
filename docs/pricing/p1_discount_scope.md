# P1.2 Discount Engine Scope

**Goal:** Apply price reductions deterministically based on rules.

## 1. Supported Discount Types (P1)
- **PERCENTAGE:** Reduces price by X% (e.g., 20% off).
- **FLAT:** Reduces price by fixed amount (e.g., $10 off).
- **TIERED:** Out of Scope for P1 (Moved to P2).

## 2. Precedence Rule (Strict Order)
1. **Manual Override** (Highest Priority - Admin Action)
2. **Campaign Discount** (e.g., Black Friday)
3. **Segment Default** (e.g., Dealer Rate)

## 3. Stacking Policy
- **Decision:** **NO STACKING**.
- Logic: "Best Price Wins" or "Priority Wins".
- **Selected:** Priority Wins (Precedence Rule above).

## 4. Application Point
- Applied to `Gross Price` **after** Free/Package allocation logic.
- Only affects `PAID` quote type.
