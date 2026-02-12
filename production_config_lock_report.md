# Production Configuration Lock Report (Plan)

**Goal:** Immutable configuration state.

## 1. Checklist
- [ ] `DEBUG=False`.
- [ ] `SECRET_KEY` rotated.
- [ ] `PRAGMATIC_SECRET` verified against provider dashboard.
- [ ] `RISK_LIMITS` set to production values.
- [ ] `ALEMBIC_HEAD` verified.

## 2. Artifacts
- Config Snapshot (redacted).
- Git Tag `v1.0.0-gold`.
