# Kullanım Kılavuzu (TR) — Operasyona Dayanıklı

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Platform Engineering / Ops  

Bu doküman, **uzun ömürlü ve ops-dayanıklı** olacak şekilde, yeni gelen birinin sözlü kültüre ihtiyaç duymadan sistemi ayağa kaldırabilmesi için hazırlanmıştır.

> EN ana kaynaktır. TR karşılığı: `/docs/new/tr/guides/user-manual.md`.

---

## İçindekiler

1. Kurulum
2. Ortamlar (dev / stage / prod)
3. Rol & Yetkilendirme Modeli (Access Control)
4. Admin Login & Tenant Lifecycle (platform owner → tenant → tenant admin)
5. Tenant Güvenliği ve İzolasyon Garantileri
6. Veri Yaşam Döngüsü
7. CI / Release Runbook
8. Upgrade / Migration Rehberi
9. Konfigürasyon & Secrets Yönetimi
10. Loglama, Audit ve İzlenebilirlik
11. Şifre Sıfırlama & Break-Glass
12. Sık Hatalar & Çözümleri
13. Performans & Limitler (Guardrails)
14. Incident & Destek Akışı

---

## 0) Buradan başla

- Quickstart (30 dk): `/docs/new/tr/guides/quickstart.md`
- Operasyonel rehber: `/docs/new/tr/guides/ops-manual.md`

---

## 1) Kurulum

Bkz:
- `/docs/new/tr/guides/install.md`
- `/docs/new/tr/guides/secrets.md`
- `/docs/new/tr/guides/migrations.md`
- `/docs/new/tr/guides/performance-guardrails.md`

---

## 2) Ortamlar (dev / stage / prod)

Bkz:
- `/docs/new/tr/guides/deployment.md`

---

## 3) Rol & Yetkilendirme Modeli (Access Control)

### 3.1 Rol tanımları (mevcut codebase)

Admin kimlik modeli `AdminUser` etrafında şekillenir:
- `is_platform_owner` — **TRUE**: platform owner / süper admin (cross-tenant)
- `tenant_id` — owner olmayan admin için tenant scope
- `tenant_role` — tenant içi rol (çoğu yerde default `tenant_admin`)

Referans:
- `backend/app/models/sql_models.py`
- `backend/app/utils/permissions.py` (`require_owner`)
- `/docs/new/tr/admin/roles-permissions.md` (rol matrisi + enforcement referansları)

### 3.2 Rol & yetki matrisi

| Rol | Scope | Tenant create | Tenant delete/purge | Tenant policy update | Audit okuma | Not |
|---|---|---:|---:|---:|---:|---|
| Platform Owner (Süper Admin) | Tüm tenant’lar | ✅ | ✅ (guard’lı) | ✅ | ✅ | `X-Tenant-ID` header ile impersonate edebilir (sadece owner) |
| Tenant Admin | Tek tenant | ❌ | ❌ | ✅ | ✅ (tenant scope) | `X-Tenant-ID` header kullanımı yasak |

> “Neden tenant admin tenant silemez?”
> - Tenant silme/purge platform seviyesinde yıkıcı bir operasyondur.
> - Kodda tenant create/list ve bazı mutation’lar `require_owner()` ile korunur.

### 3.3 Endpoint bazlı enforcement (örnek)

- Tenant endpoint’leri owner-only:
  - `POST /api/v1/tenants` → `require_owner(current_admin)`
  - `GET /api/v1/tenants` → `require_owner(current_admin)`

- Tenant admin’e açık (tenant-scope) örnek:
  - `PUT /api/v1/tenants/payments/policy` → `require_tenant_policy_admin`

---

## 4) Admin Login & Tenant Lifecycle

Bkz:
- `/docs/new/tr/admin/tenant-lifecycle.md`
- `/docs/new/tr/architecture/tenancy.md`
- `/docs/new/tr/architecture/data-lifecycle.md`
- `/docs/new/tr/architecture/audit-logging.md`

Tenant scope davranışı:
- `X-Tenant-ID` header sadece platform owner impersonation için serbest.
- Tenant admin header ile tenant override edemez.

Referans:
- `backend/app/core/tenant_context.py`

---

## 5) Tenant Güvenliği ve İzolasyon Garantileri

### 5.1 Tenant ID propagation

Tenant scope akışı:
- Request → `X-Tenant-ID` (opsiyonel, sadece owner)
- Backend → `get_current_tenant_id()`
- DB query → `tenant_id` ile filtre / resolved tenant context
- Log/audit → `tenant_id` ve `request_id`

### 5.2 Cross-tenant data leak engeli

Ana guard’lar:
- Owner olmayan admin için `X-Tenant-ID` header injection yasak.
- Route’lar tenant-scope kaynaklara erişmeden önce `get_current_tenant_id()` kullanır.

### 5.3 System tenant neden silinemez

Testler ve deterministik boot path’leri çoğu yerde stabil bir tenant id’ye (genelde `default_casino`) dayanır.
Prod’da “system tenant” korunmalıdır.

> Hard delete/purge yapılacaksa system tenant için explicit guard şarttır.

### 5.4 Soft delete vs hard delete

- **Soft delete:** kayıt durur, deleted/inactive işaretlenir
- **Hard delete:** kayıt fiziksel silinir

Finans/audit içeren sistemlerde soft delete tercih edilir.

---

## 6) Veri Yaşam Döngüsü (Data Lifecycle)

Legacy referanslar:
- `/docs/ops/backup.md`
- `/docs/ops/dr_runbook.md`
- `/docs/ops/restore_drill_proof/template.md`

Temel prensipler:
- Silme ≠ yok etme (audit/finans)
- Purge kontrollü olmalı ve loglanmalı
- Backup/restore retention ve tenant silme operasyonlarını etkiler

---

## 7) CI / Release Runbook

Bkz:
- `/docs/new/tr/runbooks/ci.md`
- `/docs/new/tr/runbooks/release.md`
- `/docs/new/tr/runbooks/ops.md`
- `/docs/new/tr/runbooks/incident.md`

---

## 8) Upgrade / Migration Rehberi

### 8.1 Sıra

Önerilen sıra:
1) Uygulama kodunu deploy et
2) DB migration (`alembic upgrade head`)
3) Kritik akışlarda smoke test

### 8.2 Geri dönüş (rollback)

- App rollback (image/container)
- DB rollback zor; şüphe varsa restore-from-backup tercih edilir

Legacy:
- `/docs/ops/dr_runbook.md`

### 8.3 Migration fail olursa

- Deploy’u durdur
- Migration loglarını topla
- Karar: hotfix migration mı, image rollback mi, restore mu?

---

## 9) Konfigürasyon & Secrets Yönetimi

### 9.1 Environment variable kuralları

- secret hardcode edilmez
- ortam bazlı ayrılır

### 9.2 Secret rotation

- payment key’leri ve JWT secret rotate edilir
- blast radius + rollback planı yazılır

### 9.3 CI/CD secrets

- CI secret manager kullan
- loglarda secret basma

---

## 10) Loglama, Audit ve İzlenebilirlik

### 10.1 Canonical log schema

Legacy:
- `/docs/ops/log_schema.md`

Önemli alanlar:
- `request_id`
- `tenant_id`

### 10.2 Audit kapsamı

En az şu event’ler audit’e düşmeli:
- tenant created/disabled/deleted
- admin login başarısız denemeler
- policy değişiklikleri
- break-glass işlemleri

---

## 11) Şifre Sıfırlama & Break-Glass

Bkz:
- `/docs/new/tr/admin/password-reset.md`

---

## 12) Sık Hatalar & Çözümleri

### 12.1 Admin login “Network Error”

Topla:
- request URL
- status code
- response body / console error

Yanlış host/protokol ise → frontend baseURL.
`/api/...` doğru gidiyor ama fail ise → proxy/backend.

### 12.2 Frozen lockfile

Bkz:
- `/docs/new/tr/runbooks/ci.md`

### 12.3 Migration sorunları

Bkz:
- Bölüm 8

---

## 13) Performans & Limitler (Guardrails)

Ayrıca:
- `/docs/new/tr/api/overview.md`
- `/docs/new/tr/api/admin.md`
- `/docs/new/tr/api/payments.md`
- `/docs/new/tr/api/webhooks.md`
- `/docs/new/tr/api/payouts.md`

### 13.1 Rate limit

Backend’de kritik endpoint’ler için basit in-memory rate limiter vardır.
Referans:
- `backend/app/middleware/rate_limit.py`

Notlar:
- dev/test ortamlarında limitler gevşektir
- prod/staging daha sıkıdır (örn login)

### 13.2 Background job’lar

- scheduler/worker altyapısı
- yüksek maliyetli operasyonlar (örn purge)

---

## 14) Incident & Destek Akışı

### 14.1 Seviyelendirme

- **P0:** tam kesinti, para hareketi blok, data integrity riski
- **P1:** ciddi bozulma, kısmi kesinti
- **P2:** kritik olmayan bug
- **P3:** küçük issue / kozmetik

### 14.2 İlk bakılacak yerler

- backend log (request_id ile korelasyon)
- audit log (kim ne yaptı)
- DB health ve migration

### 14.3 Rollback vs hotfix

- Risk yüksekse ve fix net değilse rollback
- İzole değişiklik ve doğrulanabilir fix varsa hotfix

Legacy:
- `/docs/ops/dr_runbook.md`
