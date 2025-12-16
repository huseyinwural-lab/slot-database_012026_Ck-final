# E2E Smoke Matrix (CRM + Affiliates)

Bu doküman, CRM/Affiliates için regresyonları yakalamak üzere eklenen Playwright smoke testlerini açıklar.

## Hedef
- “Load failed” türü hataları PR seviyesinde yakalamak.
- Minimal/full tenant matrix ile deterministik doğrulama.

## Testler
Playwright spec:
- `e2e/tests/crm-aff-matrix.spec.ts`

Senaryolar:
1) `default_casino` (full)
   - `/crm` açılır, ilk çağrı `/api/v1/crm/campaigns` 200
   - `/affiliates` açılır, ilk çağrı `/api/v1/affiliates` 200
2) `demo_renter` (minimal)
   - `/crm` → ModuleDisabled, API 403/503
   - `/affiliates` → ModuleDisabled, API 403/503

## Determinizm / Seed Notu
- Testler owner login ile çalışır: `admin@casino.com / Admin123!`
- Tenant context, localStorage üzerinden set edilir:
  - `impersonate_tenant_id=default_casino|demo_renter`
- Repo seed’inde bu iki tenant mevcut olmalıdır.

## CI
GitHub Actions workflow:
- `.github/workflows/prod-compose-acceptance.yml`

Fail durumunda artifact üretilir:
- `playwright trace/screenshot/video` (retain-on-failure)
- `docker compose logs` (TCK-CI-001)

## Süre hedefi
- Smoke suite hedefi: ≤ 5–7 dakika (workers=1, headless).
