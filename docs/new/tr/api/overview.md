# API Özeti (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Backend Engineering  

Bu bölüm, önemli API alanlarının kısa bir haritasını verir. Detay endpoint spesifikasyonları değişebilir; bu dosya stabil kalmalıdır.

---

## Base path

Tüm backend endpoint’leri şuradan yayınlanır:
- `/api/v1/...`

---

## Ana alanlar

- Auth: `/api/v1/auth/*`
- Tenants: `/api/v1/tenants/*`
- Admin: `/api/v1/admin/*` (bkz `admin.md`)
- Payments: `/api/v1/payments/*` (bkz `payments.md`)
- Payouts: `/api/v1/payouts/*` (bkz `payouts.md`)
- Webhook'lar: (bkz `webhooks.md`)

---

## Multi-tenancy kuralları

- Tenant context login olan admin’in `tenant_id` alanından gelir.
- Platform owner `X-Tenant-ID` ile tenant scope impersonate edebilir.
- Owner olmayanlar `X-Tenant-ID` kullanmamalıdır.

Kod referansı:
- `backend/app/core/tenant_context.py`
