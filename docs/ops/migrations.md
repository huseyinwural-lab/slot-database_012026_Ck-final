# Migrations Strategy (P3-DB-001)

## Decision
**Forward-only** migrations for staging/prod.

## Rationale
- Rollbacks are time-critical; reliably reversible migrations are hard to guarantee.
- Forward-only + hotfix minimizes downtime and reduces risk of partial reversions.

## Operational rule
- Deployments are pinned to `vX.Y.Z-<gitsha>`.
- If rollback is required and the DB schema is incompatible with the previous image:
  1) Prefer a **hotfix forward** release that restores compatibility.
  2) If not possible quickly, restore DB from backup to the last known-good point (see backup docs).

## Checklist
- Before deploy: verify `/api/ready` and plan migration window.
- After deploy: verify `/api/version`, `event=service.boot`, and smoke tests.
