# Admin API (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Backend Engineering  

Bu doküman, admin tarafı API alanlarını (admin kullanıcıları, tenant yönetimi ve ilgili governance yüzeyleri) özetler.

---

## 1) Base path

Tipik admin path’leri:
- `/api/v1/admin/*`

---

## 2) Yetkilendirme modeli

- Platform Owner (Süper Admin): `is_platform_owner = true`
- Tenant Admin: `tenant_role = tenant_admin` (tenant scope)

Kurallar:
- Owner-only operasyonlar `require_owner()` ile korunmalıdır.
- Tenant scope `get_current_tenant_id()` ile çözülür.
- `X-Tenant-ID` header yalnız owner impersonation için serbesttir.

Bkz:
- `/docs/new/tr/admin/roles-permissions.md`
- `backend/app/core/tenant_context.py`
- `backend/app/utils/permissions.py`

---

## 3) Admin kullanıcı yönetimi (tipik)

Endpoint’ler ortama göre değişebilir; ancak admin modülleri genelde şunları içerir:
- Tenant admin oluşturma/invite
- Tenant scope içinde admin listeleme
- Admin hesabı disable/enable

> Ops notu: yıkıcı aksiyonlar (disable/delete) audit’lenmelidir.

---

## 4) Audit & izlenebilirlik

Admin aksiyonları en az şu audit event’lerini üretmelidir:
- admin created/invited
- admin disabled/enabled
- failed login attempts / lockouts
- break-glass ile ilk owner oluşturma

Legacy:
- `/docs/ops/log_schema.md`
- `/docs/ops/audit.md` (varsa)
