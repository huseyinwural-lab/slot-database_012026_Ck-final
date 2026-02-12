# P1.2 Financial Reporting Smoke Test

**Date:** 2026-02-15
**Environment:** Integration / Pre-Prod
**Endpoint:** `GET /api/v1/admin/reports/financials`

## 1. Objective
Verify that the NGR (Net Gaming Revenue) report accurately reflects the underlying ledger state after applying discounts.

## 2. Test Scenario (Ledger Reconciliation)

### Input Data (Ledger State)
| Transaction ID | Type | Gross ($) | Discount ($) | Net ($) |
|----------------|------|-----------|--------------|---------|
| `tx_001` | Listing Fee | 100.00 | 20.00 | 80.00 |
| `tx_002` | Listing Fee | 50.00 | 0.00 | 50.00 |
| **TOTAL** | | **150.00** | **20.00** | **130.00** |

### API Response
```json
{
    "period": {
        "start": "2026-02-15T00:00:00",
        "end": "2026-02-15T23:59:59"
    },
    "gross_revenue": 150.00,
    "total_discounts": 20.00,
    "net_revenue": 130.00,
    "effective_discount_rate": 0.1333
}
```

## 3. Verification Checks
- [x] **Gross Match:** API `150.00` == Ledger `150.00`
- [x] **Discount Match:** API `20.00` == Ledger `20.00`
- [x] **Net Match:** API `130.00` == Ledger `130.00`
- [x] **Math Integrity:** `Gross - Discount == Net` (150 - 20 = 130)

## 4. Conclusion
**PASS**. The financial reporting endpoint is mathematically consistent with the ledger.
