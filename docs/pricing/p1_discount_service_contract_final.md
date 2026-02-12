# P1 Discount Service Contract (Final)

**Output Object:** `Quote`

```json
{
  "price": 80.00, // Net Amount (Payable)
  "type": "PAID", // or FREE, PACKAGE
  "breakdown": {
    "gross_amount": 100.00,
    "discount_amount": 20.00,
    "applied_discount": {
      "id": "uuid...",
      "code": "SUMMER_20",
      "type": "PERCENTAGE"
    }
  }
}
```

**Invariant:**
`net_amount = gross_amount - discount_amount`
`net_amount >= 0`

**Application Scope:**
- If `type` is `FREE` or `PACKAGE`: `discount_amount` MUST be 0.
