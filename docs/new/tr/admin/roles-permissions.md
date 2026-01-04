# Roller & Yetkiler (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Security / Platform Engineering  

Bu doküman, backend’in kullandığı **rol modeli** ve **enforcement (koruma) noktalarını** açıklar.

---

## 1) Terminoloji

- **Platform Owner (Süper Admin):** `AdminUser.is_platform_owner = true`
- **Tenant Admin:** genelde `AdminUser.tenant_role = "tenant_admin"` ve tek bir `tenant_id` ile sınırlıdır
- **Tenant scope:** request için çözümlenen aktif tenant context

---

## 2) Rol → yetenek matrisi

| Yetenek | Platform Owner | Tenant Admin | Not |
|---|---:|---:|---|
| Tenant listeleme | ✅ | ❌ | Owner-only (`require_owner`) |
| Tenant oluşturma | ✅ | ❌ | Owner-only (`require_owner`) |
| Tenant feature flag güncelleme | ✅ | ❌ | Owner-only (`require_owner`) |
| Tenant capabilities okuma | ✅ | ✅ | Tenant `get_current_tenant_id()` ile çözülür |
| Payments policy güncelleme (tenant) | ✅ | ✅ | `require_tenant_policy_admin` ile izinli |
| `X-Tenant-ID` ile impersonation | ✅ | ❌ | Owner olmayanlar için yasak |

---

## 3) Enforcement nerede yapılır? (kod referansları)

### 3.1 Owner-only guard

- `backend/app/utils/permissions.py`
  - `require_owner(admin)`

Örnek kullanım:
- `backend/app/routes/tenant.py`
  - `GET /api/v1/tenants` (list) → owner-only
  - `POST /api/v1/tenants` (create) → owner-only
  - `PATCH /api/v1/tenants/{tenant_id}` (feature flags) → owner-only

### 3.2 Tenant scope çözümleme guard’ı

- `backend/app/core/tenant_context.py`
  - `get_current_tenant_id(request, current_admin, session)`

Kurallar:
- `X-Tenant-ID` header sadece `is_platform_owner=true` iken serbest.
- Owner olmayan `X-Tenant-ID` gönderirse → **403 TENANT_HEADER_FORBIDDEN**.

### 3.3 Tenant-admin’e açık policy update

- `backend/app/routes/tenant.py`
  - `require_tenant_policy_admin(admin)`
  - `PUT /api/v1/tenants/payments/policy`

---

## 4) Neden tenant admin tenant silemez?

Tenant silme/purge platform seviyesinde yıkıcı bir operasyondur:
- retention/audit gereksinimlerini etkiler
- deterministik test/system tenant’ları (örn. `default_casino`) bozabilir
- bu yüzden yalnızca Platform Owner’a bırakılır

Gelecekte delete/purge endpoint’i eklenecekse:
- `require_owner` ile koru
- system tenant için explicit koruma ekle
- her aksiyonu audit’le
