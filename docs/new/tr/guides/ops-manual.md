# Operasyonel Rehber (TR)

> Platform-geneli ilk müdahale playbook’ları için: `/docs/new/tr/guides/common-errors.md`


**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Platform Engineering  

Bu rehber, gerçek hayat operasyonları içindir. Quickstart’ı tamamlar.

---

## 1) Deploy modelleri

### 1.1 Docker Compose

- Küçük ortamlar veya acceptance deploy’ları için compose kullanılabilir.
- Secret’ları compose dosyalarına gömmeyin.

Legacy:
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `/docs/CI_PROD_COMPOSE_ACCEPTANCE.md`

### 1.2 Kubernetes

- Secret manager entegrasyonu kullanın (ExternalSecrets/Vault).
- readiness/liveness probe’ları tanımlayın.
- ingress ile `/api` routing’i zorlayın.

---

## 2) Secrets yönetimi

Bkz:
- `/docs/new/tr/guides/secrets.md`

---

## 3) Gözlemlenebilirlik (minimum)

### 3.1 Loglar

- Structured log schema kullanın.
- Redaction kuralları uygulanmalı.

Bkz:
- `/docs/ops/log_schema.md`
- `/docs/new/tr/architecture/audit-logging.md`

### 3.2 Metrikler / izleme (tracing)

Eğer tam implement değilse minimum:
- 5xx hata oranı
- webhook failure oranı
- payout status transition süresi

---

## 4) Backup / restore & veri yaşam döngüsü

Bkz:
- `/docs/new/tr/architecture/data-lifecycle.md`
- `/docs/new/tr/runbooks/ops.md`

---

## 5) Incident runbook’ları

Bkz:
- `/docs/new/tr/runbooks/incident.md`

---

## 6) Release checklist + rollback

Bkz:
- `/docs/new/tr/runbooks/release.md`
- `/docs/new/tr/runbooks/release-readiness-checklist.md`

---

## 7) Multi-tenant lifecycle

Bkz:
- `/docs/new/tr/admin/tenant-lifecycle.md`
- `/docs/new/tr/architecture/tenancy.md`

Garantiler:
- platform owner tenant oluşturur
- tenant admin tenant silemez
- system tenant korunur

---

## 8) Break-glass

Bkz:
- `/docs/new/tr/runbooks/password-reset.md`
- `/docs/new/tr/runbooks/break-glass.md`
- `/docs/new/tr/architecture/audit-logging.md`

Politika:
- break-glass aksiyonları zaman-bounded ve audit’li olmalıdır
