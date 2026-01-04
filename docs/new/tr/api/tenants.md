# Tenants API (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Backend Engineering  

---

## Owner-only endpoint’ler

- `GET /api/v1/tenants` — tenant listeleme
- `POST /api/v1/tenants` — tenant oluşturma
- `PATCH /api/v1/tenants/{tenant_id}` — feature flag güncelleme

Enforcement:
- `require_owner()`
- `backend/app/utils/permissions.py`

---

## Tenant-scope endpoint’ler

- `GET /api/v1/tenants/capabilities`
- `GET /api/v1/tenants/payments/policy`
- `PUT /api/v1/tenants/payments/policy`

Tenant çözümleme:
- Owner `X-Tenant-ID` ile override/impersonation yapabilir
- Owner olmayanlar header kullanamaz

Bkz:
- `/docs/new/tr/admin/roles-permissions.md`
- `backend/app/core/tenant_context.py`
