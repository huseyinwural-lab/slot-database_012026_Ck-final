# P1 Discount Cutover Verification

**Test Plan:** A/B Comparison.

## Scenario 1: Flag OFF
- Input: `User(segment=DEALER)`, `Listing(PAID)`
- Expected:
  - `Quote.price` = Base Rate.
  - `Quote.details.discount_amount` = None/0.
  - Ledger: `amount` = Base Rate, `discount_amount` = 0.

## Scenario 2: Flag ON
- Input: `User(segment=DEALER)`, `Listing(PAID)`, `Active Discount(20%)`
- Expected:
  - `Quote.price` = Base Rate * 0.8.
  - `Quote.details.discount_amount` = Base Rate * 0.2.
  - `Quote.details.gross_amount` = Base Rate.
  - Ledger: `amount` = Net, `discount_amount` = 0.2 * Base.

**Verification Status:** Pending Integration Test run.
