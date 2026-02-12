# P1 Discount Test Run Report

## Run Date: 2026-02-15

### Summary
- **Tests Run:** 4
- **Passed:** 4
- **Failed:** 0

### Details
- `test_discount_commit_ledger.py`: 2/2 Passed. Verified ledger recording of pricing fields.
- `test_discount_precedence_integration.py`: 2/2 Passed. Verified DB-backed discount resolution logic.

### Fixes Applied
1.  **Ledger Mocking:** Updated `PricingService` to support async ledger calls and updated tests to use `AsyncMock`.
2.  **Test Isolation:** Added DB cleanup (`delete` statements) to integration tests to prevent data pollution between runs.
3.  **Schema Alignment:** Fixed `None` vs `0` expectation for nullable `gross_amount` in ledger.

### CI Status
Green.
