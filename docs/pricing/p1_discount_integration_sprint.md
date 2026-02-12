# P1.2 Integration & Test Sprint

**Goal:** Green CI for both V1 (Legacy) and V2 (Discount) modes.

## Sprint Backlog
1. **Migration Apply:** Run `alembic upgrade head` and validate schema.
2. **Flag Implementation:** `PRICING_ENGINE_V2_ENABLED` logic in `PricingService`.
3. **Ledger Update:** Ensure `record()` supports new columns with backward compatibility.
4. **Test Execution:** Run full suite with flag OFF (Baseline) and ON (New Logic).
5. **Observability Check:** Verify metrics emission.

## Success Criteria
- [ ] Migration applied without downtime.
- [ ] V1 mode passes regression tests.
- [ ] V2 mode passes new discount scenarios.
- [ ] No regressions in core listing flow.
