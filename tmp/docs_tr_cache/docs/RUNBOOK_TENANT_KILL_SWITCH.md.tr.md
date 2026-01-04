# RUNBOOK-002 — Tenant Kill Switch

## Amaç
Belirli bir tenant’ta belirli bir modülü geçici olarak devre dışı bırakmak.

## Veri Şeması
Tenant.features içine:
```json
{
  "kill_switches": {
    "crm": true,
    "affiliates": false,
    "experiments": true
  }
}
```

## Uygulama (Owner ile)

### Endpoint
`POST /api/v1/kill-switch/tenant`

Payload:
```json
{
  "tenant_id": "demo_renter",
  "module_key": "crm",
  "disabled": true
}
```

Örnek curl:
```bash
API_URL=https://api.example.com
TOKEN=<OWNER_JWT>

curl -i -X POST "$API_URL/api/v1/kill-switch/tenant" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"demo_renter","module_key":"crm","disabled":true}'
```

## Doğrulama
- Aynı tenant context’inde ilgili modül endpoint’i 503 dönmeli:
```bash
curl -i "$API_URL/api/v1/crm/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: demo_renter"
```
Beklenen:
- HTTP 503
- `error_code=MODULE_TEMPORARILY_DISABLED`
- `module=crm`
- `reason=tenant_kill_switch`

## Audit / Log beklentisi
- Beklenen log alanları (JSON):
  - timestamp, level, message
  - request_id
  - tenant_id
  - path, method, status_code, duration_ms
- Kill switch çağrısı için ayrıca audit kaydı önerilir (kim/ne zaman/hangi tenant/modül).

Not: Bu repo’da audit servisi mevcut. Patch 3/sonrası için “kill switch update” olayının audit’e eklenmesi önerilir.
