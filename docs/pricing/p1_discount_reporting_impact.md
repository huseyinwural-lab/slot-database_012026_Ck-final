# P1 Discount Reporting Impact

**Goal:** Ensure financial transparency (NGR).

## 1. Ledger Schema Update
Current: `amount` (Implicitly Net).
New:
- `gross_amount`: Base price before discount.
- `discount_amount`: Reduction value.
- `net_amount`: Final charge (gross - discount).
- `applied_discount_id`: Traceability.

## 2. NGR Calculation
`NGR = SUM(net_amount)`

## 3. Discount Budgeting
- Admin report required: "How much revenue did we forego via Discount X?"
- Query: `SUM(discount_amount) WHERE applied_discount_id = X`

## 4. Invariant
`gross_amount - discount_amount == net_amount` (Must be enforced at DB or Service level).
