# Ledger & PSP Secrets / Env Checklist

Bu checklist, `ledger_enforce_balance` ve webhook imza doğrulaması
(`webhook_signature_enforced`) prod/staging rollout'undan önce doğru
konfigürasyonun sağlandığını kontrol etmek için kullanılır.

## 1. Ledger Feature Flags

- [ ] `ledger_shadow_write` istenen değerde mi?
  - Öneri: Prod'da **True** (ledger her zaman shadow write alsın).
- [ ] `ledger_enforce_balance` default **False** mu?
  - Rollout'tan önce global config bu şekilde olmalı.
  - Enforce yalnızca planlı rollout sırasında açılmalı.
- [ ] `ledger_balance_mismatch_log` **True** mu?
  - Rollout süresince mutlaka açık olmalı (telemetry için).

## 2. Webhook / PSP Ayarları

- [ ] `webhook_secret_mockpsp` env'de set edildi mi?
  - MockPSP için bile production/staging'de rastgele/güçlü bir secret kullanılmalı.
- [ ] `webhook_signature_enforced` default **False** mu?
  - İlk rollout'ta, önce MockPSP ile düşük riskli ortamda test edin.
  - Signature enforcement, runbook'ta tarif edilen adımlarla kademeli açılmalı.

## 3. OPS-01 Backfill Hazırlığı

- [ ] `python -m backend.scripts.backfill_wallet_balances --dry-run` staging'de çalıştırıldı mı?
- [ ] Dry-run çıktısı incelendi mi?
  - `created`, `skipped_exists`, `updated_forced`, `errors` değerleri beklenen aralıklarda mı?
- [ ] Gerçek backfill (`--dry-run` olmadan) staging'de başarıyla çalıştı mı?

## 4. Rollout Öncesi Regresyon Testleri

- [ ] Backend testleri:

```bash
cd /app/backend
pytest -q \
  tests/test_ledger_repo.py \
  tests/test_ledger_shadow_flows.py \
  tests/test_ledger_enforce_balance.py \
  tests/test_ledger_concurrency_c1.py \
  tests/test_psp_mock_adapter.py \
  tests/test_psp_ledger_integration.py \
  tests/test_psp_webhooks.py \
  tests/test_ops_backfill_wallet_balances.py
```

- [ ] E2E smoke (withdrawals):

```bash
cd /app/e2e
yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts
```

## 5. Rollout Sırasında İzlenecek Ek Sinyaller

- [ ] 400 `INSUFFICIENT_FUNDS` oranı (öncesi/sonrası karşılaştırması).
- [ ] Webhook 401 (`WEBHOOK_SIGNATURE_INVALID`) oranı.
- [ ] ledger_balance_mismatch telemetrisinin seviyesi ve trendi.

## 6. Rollback Hazırlığı

- [ ] Rollback prosedürü (ledger-rollout-runbook.md içindeki bölüm) ekibe anlatıldı mı?
- [ ] Konfig değerleri rollback için hazır mı?
  - `LEDGER_ENFORCE_BALANCE=False`
  - `WEBHOOK_SIGNATURE_ENFORCED=False`
- [ ] Rollback sonrası yeniden çalıştırılacak test komutları net mi?
  - Backend regresyon
  - E2E smoke
