# Release Gates (P1)

**Policy:** P1 code cannot be merged/deployed to production until these gates are passed.

## Gate 1: Integrity Check
- [ ] `docs/pricing/integrity_guards.md` verified against DB Schema.
- [ ] No missing Unique Constraints.
- [ ] No missing Check Constraints.

## Gate 2: Parity Check
- [ ] `docs/pricing/prod_parity_checklist.md` completed.
- [ ] Postgres-specific smoke tests passed in Staging.

## Gate 3: Observability Ready
- [ ] Metrics defined in `docs/pricing/observability_spec.md` are instrumented in code.
- [ ] Dashboard draft created (or logs verified).

## Gate 4: Test Coverage
- [ ] P1 Strategy Matrix (`docs/pricing/p1_test_strategy.md`) 100% covered.
- [ ] No regression in T2 suite.
