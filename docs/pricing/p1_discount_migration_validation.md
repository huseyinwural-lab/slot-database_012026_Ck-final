# P1 Discount Migration Validation

**Objective:** Ensure schema integrity post-migration.

## 1. Schema Check
- Table `discounts` exists.
- Table `discount_rules` exists.
- Table `pricing_ledger` has columns: `gross_amount`, `discount_amount`, `applied_discount_id`.

## 2. Constraint Check
- `discount_rules.priority` defaults to 0.
- `discounts.code` is unique.
- `pricing_ledger.discount_amount` is NOT NULL (default 0).

## 3. Backfill Strategy (Implicit)
- Existing ledger rows will have `gross_amount=NULL` initially.
- **Decision:** Do NOT backfill history. Only enforce `NOT NULL` for NEW rows (application level) or allow nullable DB columns but treat as `amount` if null in code.
- **Reporting:** Views/Queries must handle `COALESCE(gross_amount, amount)`.
