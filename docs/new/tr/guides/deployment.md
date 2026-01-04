# Deploy Rehberi (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Platform Engineering  

Bu rehber **üst seviye** deploy akışını özetler. Repo içinde `/docs/ops/` ve `/docs/payments/` altında kapsamlı legacy runbook’lar bulunur.

---

## 1) Ortamlar

Tipik ortamlar:
- **dev** (local)
- **staging**
- **prod**

Proje kuralı:
- `ENV=prod|staging` veya `CI_STRICT=1` iken SQLite kabul edilmez ve **PostgreSQL DATABASE_URL zorunludur**.

---

## 2) Gerekli konfigürasyon

- `DATABASE_URL` (PostgreSQL)
- JWT secret (prod güvenli)
- Payment provider anahtarları (Stripe/Adyen)
- `/api` routing için reverse proxy ayarları

> URL/port kod içine hardcode edilmemeli; environment variable kullanılmalı.

---

## 3) Docker tabanlı deploy

Referans (legacy):
- `/docs/DOCKER_PROD_ACCEPTANCE_RUNBOOK.md`
- `/docs/CI_PROD_COMPOSE_ACCEPTANCE.md`

---

## 4) Migration

Yeni backend versiyonu deploy edilmeden önce:

```bash
cd backend
alembic upgrade head
```

---

## 5) Observability / Ops

Legacy ops:
- `/docs/ops/observability.md`
- `/docs/ops/alerts.md`
- `/docs/ops/rollback.md`

---

## 6) Release kanıt paketi

- `/docs/RELEASE_EVIDENCE_PACKAGE.md`
- `/docs/release-checklist.md`
