# SEC-001 — Yetki Matrisi + Impersonation (X-Tenant-ID)

## Hedef
- `X-Tenant-ID` header’ı yalnızca **Platform Owner** için impersonation amaçlı kullanılabilir.
- Tenant admin, header ile başka tenant verisine erişemez.

## Kural
`backend/app/utils/tenant.py`:
- `X-Tenant-ID` sadece `admin.is_platform_owner == True` ise dikkate alınır.
- Aksi halde tenant context `admin.tenant_id` üzerinden belirlenir.

## Yetki Matrisi (minimum)
- `can_use_kill_switch`: yalnız owner/enterprise
- `can_manage_experiments`: owner-only
- `can_manage_affiliates`: tenant bazlı olabilir
- `can_use_crm`: tenant bazlı olabilir

## Doğrulama Senaryosu (manual)
1) Owner ile login → `X-Tenant-ID=demo_renter` header’ı ile capabilities çağır:
   - tenant_id demo_renter dönmeli
2) Tenant admin ile login → `X-Tenant-ID=default_casino` header’ı ile capabilities çağır:
   - tenant_id demo_renter kalmalı (override olmamalı)

Beklenen: veri sızıntısı yok.

## Notlar
- Frontend’de impersonation header’ı localStorage ile set ediliyor.
- Owner dışında kullanıcılar için header’ı göndermek zararsız olmalı; backend ignore eder.
