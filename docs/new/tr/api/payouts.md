# Çekimler (Payouts) API (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Payments Engineering  

Bu doküman, payout (çekim/ödeme) tarafındaki endpoint’leri ve status polling davranışının operasyonel notlarını içerir.

---

## 1) Tipik endpoint’ler

Ortamınıza göre payout endpoint’leri şunları içerebilir:
- `GET /api/v1/payouts/status/{tx_id}` — payout status polling
- `POST /api/v1/payouts/*` — payout başlatma/yönetme

> Bazı ortamlarda payout’lar `/api/v1/payments/*` altında bulunabilir. Bu dosya “stabil harita” amaçlıdır.

---

## 2) Status polling (ops notları)

Payout akışları genellikle asenkron olur:
- payout oluşturulur
- provider işlemleri background’da sürer
- client final duruma gelene kadar status poll yapar

CI/E2E’de sık görülen flakiness:
- polling sırasında geçici network hataları (`socket hang up`, timeout)

Ops önerisi:
- bounded timeout + retry ile deterministik poll uygulanmalı.
- backend log’larında `request_id` ile korelasyon yapılmalı.

Legacy:
- `/docs/E2E_SMOKE_MATRIX.md`
- `/docs/ops/webhook-failure-playbook.md`

---

## 3) Tenant scope

- Tüm payout aksiyonları tenant-scope olmalıdır.
- Owner `X-Tenant-ID` ile tenant impersonation yapabilir.

Bkz:
- `/docs/new/tr/api/tenants.md`
- `/docs/new/tr/admin/roles-permissions.md`
- `backend/app/core/tenant_context.py`
