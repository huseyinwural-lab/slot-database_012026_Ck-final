# Upgrade / Migration Guide (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Backend Engineering / Ops  

This guide explains the safe order of operations for schema and code upgrades.

---

## 1) Golden rules

1) Treat migrations as production changes
2) Prefer forward-only migrations
3) Always have a rollback plan (app rollback + DB restore)

---

## 2) Order of operations

Recommended order:

1) Confirm target environment and maintenance window (if needed)
2) Deploy backend image (or ensure new code is available)
3) Run migrations
4) Run smoke checks

---

## 3) Running migrations

Typical command:

```bash
cd backend
alembic upgrade head
```

If migrations are automated in CI/CD:
- ensure logs are captured as evidence

---

## 4) If a migration fails

Immediate actions:
- stop further rollout
- capture full migration output
- confirm DB integrity

Decision:
- **Rollback app** if failure is code-level and old version can run without new schema
- **Hotfix migration** if failure is in migration logic and can be fixed quickly
- **Restore DB from backup** if integrity is in doubt

Legacy DR reference:
- `/docs/ops/dr_runbook.md`

---

## 5) Tenant-specific migration risks

Multi-tenant risks:
- long-running migrations on large tenants
- lock contention

Mitigations:
- run off-peak
- use batched backfills
- add progress logging

---

## 6) Evidence for release gate

Attach:
- git SHA
- migration output
- smoke test results
