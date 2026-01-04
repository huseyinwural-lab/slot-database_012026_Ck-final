# Multi-Tenancy (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Backend Engineering  

Bu doküman, tenant izolasyonu ve cross-tenant erişimi engelleyen kuralları açıklar.

---

## 1) Tenant scope çözümleme

Tenant scope her request için çözülür:
- Platform owner `X-Tenant-ID` ile impersonate edebilir
- Tenant admin header ile tenant override edemez

Referans:
- `backend/app/core/tenant_context.py`

---

## 2) Boundary garantileri

Beklenen garantiler:
- cross-tenant read/write yok
- audit/log kayıtlarında tenant context var

---

## 3) System tenant

Bazı deployment’larda deterministik tenant id (örn `default_casino`) boot/test için kullanılır.
Bu tenant destructive operasyonlardan korunmalıdır.

---

## 4) Tenant admin neden kısıtlı?

Tenant admin’ler platform seviyesinde aksiyonlardan bilinçli olarak alıkonur:
- tenant oluşturma
- tenant delete/purge

Bkz:
- `/docs/new/tr/admin/roles-permissions.md`
