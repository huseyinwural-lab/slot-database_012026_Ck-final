# P1 Discount Observability Run Report

**Date:** Current
**Env:** Staging (Live Traffic Simulation)

## 1. Metrics Check
- `discount_applied_total` (ON): Expected > 0. Actual: TBD.
- `discount_applied_total` (OFF): Expected 0. Actual: TBD.

## 2. Logs Check
- Search: `event="quote_calculated"`
- Flag ON: Includes `discount_code`.
- Flag OFF: Missing/Null `discount_code`.

**Result:** Pending Verification.
