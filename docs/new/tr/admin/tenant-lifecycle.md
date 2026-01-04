# Tenant Yaşam Döngüsü (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Platform Owner / Ops  

Hedef: Prod’a uygun akışta **Platform Owner (Süper Admin)** tenant oluşturur ve tenant yönetimini devreder.

---

## Kavramlar

- **Platform Owner (Süper Admin):** `AdminUser.is_platform_owner = true`
- **Tenant:** oyunlar, finans, ayarlar, adminler, oyuncular için izole scope
- **Tenant Admin:** belirli bir tenant’a bağlı admin kullanıcı

---

## Önerilen akış

1) Platform Owner login olur
2) Platform Owner Tenant oluşturur
3) Platform Owner Tenant Admin oluşturur (veya invite)
4) Tenant Admin operasyon ayarlarını yapar (payments, limitler, personel)

---

## Test notu

Bazı CI/E2E akışlarında `default_casino` gibi deterministik tenant id kullanılır.
Bu test kolaylığıdır; prod akışının yerine geçmez.

Legacy referans:
- `/docs/TENANT_ADMIN_FLOW.md`
- `/docs/manuals/PLATFORM_OWNER_GUIDE.md`
- `/docs/manuals/TENANT_ADMIN_GUIDE.md`
