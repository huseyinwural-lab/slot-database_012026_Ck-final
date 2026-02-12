# Production Parity Checklist (Post-T2)

**Objective:** Ensure behavior observed in SQLite (Test) matches PostgreSQL (Production) to prevent regression.

## 1. Data Types & Constraints
- [ ] **UUID Handling:** Verify `uuid` generation logic. SQLite stores as string, Postgres as native UUID. Ensure drivers handle conversion correctly.
- [ ] **String Length:** SQLite ignores VARCHAR(n) limits. Postgres enforces them. Verify all string fields have appropriate length validation in Pydantic models.
- [ ] **Case Sensitivity:** Verify uniqueness constraints (e.g., `email`, `sku`) behave consistently (CI/AS collation vs default).
- [ ] **Date/Time:** Ensure Timezone-aware datetimes are enforced. SQLite is naive by default; Postgres requires strict TZ handling.

## 2. Concurrency & Isolation
- [ ] **Transaction Isolation:** Verify behavior under `READ COMMITTED` (Postgres default) vs SQLite's locking mechanism.
- [ ] **Row Locking:** Verify `SELECT FOR UPDATE` behavior. SQLite locks the file; Postgres locks the row. Ensure no deadlocks in high-concurrency ledger inserts.

## 3. Database Features
- [ ] **Constraint Naming:** Ensure constraint names (FK, Unique) are consistent or explicitly named in Alembic/SQLModel to avoid auto-generated name mismatches during migration.
- [ ] **Indexing:** Verify index creation syntax compatibility.

## 4. Smoke Test Plan (Staging/Prod)
- [ ] Run `Pricing Commit` with 10 concurrent requests (Idempotency check).
- [ ] Run `Quota Allocation` boundary tests (Negative check).
- [ ] Verify `Audit Log` persistence after rollback (if applicable).
