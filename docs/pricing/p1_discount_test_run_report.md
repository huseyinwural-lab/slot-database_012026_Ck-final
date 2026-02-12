# P1 Discount Test Run Report

**Date:** Current
**Env:** CI / Staging

## 1. Unit Tests
| Suite | Result | Notes |
| :--- | :---: | :--- |
| `test_discount_logic.py` | PENDING | Logic checks |
| `test_discount_commit_ledger.py` | PENDING | Ledger format |

## 2. Integration Tests
| Suite | Result | Notes |
| :--- | :---: | :--- |
| `test_discount_precedence_integration.py` | PENDING | DB precedence |
| `test_listing_pricing_atomicity_discount.py` | PENDING | Rollback check |

## 3. Parity Check (Flag OFF)
- **Scenario:** Create listing (Dealer) with Flag OFF.
- **Expected:** Base Price.
- **Actual:** TBD.

## 4. Discount Check (Flag ON)
- **Scenario:** Create listing (Dealer) with Flag ON + Discount.
- **Expected:** Net Price.
- **Actual:** TBD.

**Blockers:** None currently reported.
