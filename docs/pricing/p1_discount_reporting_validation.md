# P1 Discount Reporting Validation

**Endpoint:** `GET /api/v1/admin/reports/financials`

## Scenario: Ledger Aggregation
We validated the reporting endpoint against the ledger data generated during the integration tests.

### Test Data
- **Transaction:** Listing Fee
- **Gross:** $100.00
- **Discount:** $20.00 (Flat)
- **Net:** $80.00

### API Response Verification
```json
{
    "period": { "start": "...", "end": "..." },
    "gross_revenue": 100.00,
    "total_discounts": 20.00,
    "net_revenue": 80.00,
    "effective_discount_rate": 0.20
}
```

## Status
**PASS**. The reporting endpoint correctly aggregates the new ledger columns (`gross_amount`, `discount_amount`, `net_amount`).

## Recommendations
- Ensure the frontend Admin Dashboard is updated to consume this new endpoint for the "Financials" tab.
