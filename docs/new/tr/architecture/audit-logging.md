# Loglama & Audit (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Security  

Bu doküman, structured log ve audit gereksinimlerini birleştirir.

---

## 1) Structured log

Canonical schema:
- `/docs/ops/log_schema.md`

Önemli alanlar:
- `request_id`
- `tenant_id`

---

## 2) Audit event’leri (minimum set)

Audit en az şunları kapsamalı:
- tenant.created / tenant.disabled / tenant.deleted
- admin login başarısız denemeler
- policy değişiklikleri
- break-glass aksiyonları

Kod referans:
- `backend/app/services/audit.py` (varsa)
- `backend/app/routes/tenant.py` gibi route içi audit çağrıları

---

## 3) Break-glass loglama

DB’den manuel super admin oluşturma veya acil değişiklikler:
- zaman-bounded
- review’lü
- log’lu olmalıdır (en az ops ticket + mümkünse audit kaydı)

---

## 4) Privacy / redaction

Asla loglama:
- şifre
- bearer token
- secret

Bkz redaction:
- `/docs/ops/log_schema.md`
