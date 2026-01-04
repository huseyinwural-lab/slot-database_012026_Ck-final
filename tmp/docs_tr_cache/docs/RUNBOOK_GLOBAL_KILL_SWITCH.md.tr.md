# RUNBOOK-001 — Global Kill Switch (KILL_SWITCH_ALL)

## Amaç
Acil durumlarda (prod) **core olmayan** modülleri tek ENV ile devre dışı bırakmak.

## Canonical ENV
```bash
KILL_SWITCH_ALL=true
```

## Neyi kapatır?
`backend/app/constants/feature_catalog.py` içindeki `non_core=true` olan modüller.
Bu projede (minimum):
- experiments (Feature Flags & A/B Testing)
- kill_switch
- affiliates
- crm

## Beklenen davranış
- Backend:
  - non-core modül endpointleri **503** döner
  - error_code: `MODULE_TEMPORARILY_DISABLED`
- UI:
  - Menü/route gating nedeniyle kullanıcı genellikle “ModuleDisabled” görür.
  - Eğer kullanıcı sayfaya girmişse API 503 üzerinden anlamlı hata görür.

## Uygulama (5 dk)
1) ENV ekle/değiştir: `KILL_SWITCH_ALL=true`
2) Deploy/restart (kendi altyapınızın prosedürü)
3) Doğrulama:
   - `/api/health` 200
   - `/api/ready` 200
   - Örnek: `/api/v1/crm/` çağrısı 503

Örnek curl:
```bash
curl -i https://api.example.com/api/v1/crm/ -H "Authorization: Bearer <token>"
```

## Rollback
1) `KILL_SWITCH_ALL=false` (veya env’i kaldır)
2) Redeploy
3) Aynı endpoint artık 200/403 (feature flag’e göre) dönmeli.

## Risk notları
- Kill switch “core” akışları etkilememeli: login/health/ready çalışmaya devam eder.
- Bu mekanizma feature flag yerine acil durum içindir; kalıcı yetkilendirme için feature flag kullanın.
