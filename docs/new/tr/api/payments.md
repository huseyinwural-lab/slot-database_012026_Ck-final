# Payments API (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Payments Engineering  

Bu doküman, ödeme (payments) tarafındaki API yüzeyinin stabil bir özetini verir.

> Provider özel prosedürler (Stripe/Adyen), webhook detayları ve incident playbook’ları şimdilik legacy `/docs/payments/` ve `/docs/ops/` altında tutulmaktadır.

---

## 1) Base path’ler

Tipik path’ler:
- `/api/v1/payments/*`
- `/api/v1/payouts/*` (ortama göre)

---

## 2) Webhook’lar (external → backend)

### 2.1 Stripe
- `POST /api/v1/payments/stripe/webhook`

### 2.2 Adyen
- `POST /api/v1/payments/adyen/webhook`

Ops notları:
- Webhook endpoint’leri genellikle **yüksek hacimli** olur; rate limit buna göre ayarlanmalıdır.
- staging/prod’da webhook signature verification açık olmalıdır.

Legacy referans:
- `/docs/payments/STRIPE_WEBHOOKS.md`
- `/docs/payments/ADYEN_WEBHOOKS.md`

---

## 3) Tenant scope & izolasyon

Kurallar:
- Tenant-scope payment policy `get_current_tenant_id()` ile çözülür.
- Platform owner `X-Tenant-ID` ile tenant impersonation yapabilir.
- Owner olmayanlar header kullanamaz.

Bkz:
- `/docs/new/tr/api/tenants.md`
- `/docs/new/tr/admin/roles-permissions.md`

---

## 4) Sık hata tipleri (ops hızlı harita)

- Webhook signature mismatch
- Provider timeout / retry storm
- Payout status polling flakiness

Legacy runbook:
- `/docs/ops/webhook-failure-playbook.md`
- `/docs/ops/dr_runbook.md`
