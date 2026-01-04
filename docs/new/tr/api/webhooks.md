# Webhook’lar (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Payments Engineering / Ops  

Bu doküman, webhook’ların operasyonel gereksinimlerini ve staging/prod ortamlarında beklenen deterministik davranışları bir araya getirir.

---

## 1) Webhook neyi garanti etmeli?

### 1.1 Doğruluk/kimlik (signature verification)
- Stripe: `Stripe-Signature` doğrulaması
- Adyen: HMAC signature doğrulaması (Adyen webhook spec)

**Kural:** staging/prod’da signature verification açık olmalıdır.

### 1.2 Idempotency
Webhook deliver’ları tekrar edebilir.

**Kural:** provider event id / notification id bazında idempotent işlenmelidir.

### 1.3 İzlenebilirlik
Her webhook request’inde:
- `request_id`
- `tenant_id` (uygulanıyorsa)
- structured log alanları

Bkz:
- `/docs/ops/log_schema.md`

---

## 2) API endpoint’leri (tipik)

- `POST /api/v1/payments/stripe/webhook`
- `POST /api/v1/payments/adyen/webhook`

Ayrıca:
- `/docs/new/tr/api/payments.md`

---

## 3) Retry stratejisi & hata yönetimi

### 3.1 Provider retry
Provider’lar non-2xx ve timeout durumunda retry yapar.

Ops önerisi:
- Verification + güvenli persistence olmadan 2xx dönme.
- DB down ise fail-fast (provider retry eder).

### 3.2 Sık hata tipleri
- Signature mismatch
- Clock skew (signature timestamp window)
- Payload schema değişiklikleri
- Duplicate event’ler

---

## 4) Tenant scope

Webhook tenant çözümleme, platformun provider hesaplarını tenant’lara nasıl map ettiği ile ilgilidir.

Kurallar:
- Owner olmayan adminlerden tenant override kabul etme.
- Public webhook endpoint’lerinde `X-Tenant-ID` kullanmaktan kaçın (secure mapping yoksa).

---

## 5) Incident playbook (hızlı)

1) Provider dashboard’larda delivery attempt’leri doğrula (Stripe/Adyen)
2) Backend log’larda `request_id` ve webhook event adını ara
3) Signature secret konfigürasyonunu doğrula
4) İşleme fail ise containment: gerekiyorsa payout otomasyonunu durdur

Legacy:
- `/docs/ops/webhook-failure-playbook.md`
- `/docs/payments/STRIPE_WEBHOOKS.md`
- `/docs/payments/ADYEN_WEBHOOKS.md`
