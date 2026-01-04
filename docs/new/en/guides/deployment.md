# Deployment Guide (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Platform Engineering  

This guide is the **high-level** deployment path. The repo contains extensive legacy production runbooks under `/docs/ops/` and `/docs/payments/`.

---

## 1) Environments

Typical environments:
- **dev** (local)
- **staging**
- **prod**

Key rule (project convention):
- In `ENV=prod|staging` or `CI_STRICT=1`, SQLite is forbidden and **PostgreSQL DATABASE_URL is required**.

---

## 2) Required configuration

- `DATABASE_URL` (PostgreSQL)
- JWT secret keys (production-safe)
- Payment provider keys (Stripe/Adyen)
- Reverse proxy config for `/api` routing

> Never hardcode URLs/ports in code; use environment variables.

---

## 3) Docker-based deployment

The project includes production compose files and acceptance workflows.

Start point (legacy):
- `/docs/DOCKER_PROD_ACCEPTANCE_RUNBOOK.md`
- `/docs/CI_PROD_COMPOSE_ACCEPTANCE.md`

---

## 4) Database migrations

Before deploying a new backend version:

```bash
cd backend
alembic upgrade head
```

---

## 5) Observability / Ops

See legacy ops docs:
- `/docs/ops/observability.md`
- `/docs/ops/alerts.md`
- `/docs/ops/rollback.md`

---

## 6) Release evidence

Release and evidence pack references:
- `/docs/RELEASE_EVIDENCE_PACKAGE.md`
- `/docs/release-checklist.md`
