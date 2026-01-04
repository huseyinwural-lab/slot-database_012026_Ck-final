# RC Kapanış Özeti — Ledger + MockPSP Paketi

Bu dosya, casino finance/wallet paneli için **Release Candidate (RC)** durumunu tek sayfada özetlemek ve PR açıklaması olarak kopyala-yapıştır kullanmak üzere hazırlanmıştır.

---

## 1) Kapsam ve RC Tanımı

Bu RC, aşağıdaki alanları kapsar:

- **LEDGER-02B**: Ledger’ın canonical hale gelmesi ve withdraw flow için `ledger_enforce_balance` altyapısı.
- **PSP-01/02/03**: MockPSP sağlayıcısı, webhook endpoint’i ve reconciliation akışı.
- **OPS-01/02**: Backfill script’i, rollout runbook/matrix ve secrets checklist.

**Amaç**: Staging / prod ortamlarında ledger tabanlı wallet mimarisini ve MockPSP entegrasyonunu **güvenli şekilde devreye alabilecek** bir RC düzeyi sağlamak.

---

## 2) Tamamlanan Epikler

### LEDGER-02B — Ledger Enforce Withdraw Flow

- Ledger transaction ve wallet snapshot modeline güvenen withdraw flow.
- `ledger_enforce_balance` feature flag ile **ledger bazlı bakiye kontrolü** (Player tablosu yerine `walletbalance`).
- `SELECT ... FOR UPDATE` ile pessimistic row lock (concurrency hardening).
- Shadow write + created-gated delta pattern ile idempotent/birimsel güncellemeler.
- Testler:
  - `backend/tests/test_ledger_enforce_balance.py`
  - `backend/tests/test_ledger_concurrency_c1.py`
  - `backend/tests/test_ledger_concurrency_c2_postgres.py` (**yalnızca Postgres / gate**, aşağı bkz.)

### PSP-01 — MockPSP Adapter

- `backend/app/services/psp/psp_interface.py`
- `backend/app/services/psp/mock_psp.py`
- Deposit/withdraw akışı içinde MockPSP ile çalışan adaptor katmanı.
- Deterministik davranış, testlere uygun sahte event/response yapısı.

### PSP-02 — Webhook Receiver + Idempotency

- Canonical webhook endpoint: `POST /api/v1/payments/webhook/{provider}`
  - Replay guard / idempotency: provider event id bazlı unique constraint
  - Signature framework: `webhook_signature_enforced` feature flag ile kontrollü enforce.
- Event mapping:
  - `deposit_captured` → ledger credit + snapshot update
  - `withdraw_paid` → ledger debit + snapshot update
- Testler:
  - `backend/tests/test_psp_webhooks.py`
  - `backend/tests/test_psp_mock_adapter.py`
  - `backend/tests/test_psp_ledger_integration.py`

### PSP-03 — Reconciliation MVP

- `reconciliation_findings` tablosu (MIG-01 ile tamamen zincire bağlı):
  - `id, provider, tenant_id, player_id, tx_id, provider_event_id, provider_ref, finding_type, severity, status, message, raw`
  - Unique: `(provider, provider_event_id, finding_type)`
- Reconciliation job:
  - `backend/app/jobs/reconcile_psp.py` — MockPSP vs ledger karşılaştırma
- Admin API:
  - `GET /api/v1/payments/reconciliation/findings`
  - `POST /api/v1/payments/reconciliation/findings/{id}/resolve`
  - `POST /api/v1/payments/reconciliation/run`
- Testler:
  - `backend/tests/test_psp_reconciliation.py`
  - `backend/tests/test_psp_reconciliation_api.py`
  - `backend/tests/test_reconciliation_model.py`

### OPS-01 — Backfill Script (WalletBalance Snapshot)

- Script: `backend/scripts/backfill_wallet_balances.py`
- Özellikler:
  - `--dry-run` (zorunlu ilk adım)
  - `--tenant-id` ile tenant scoped koşum
  - `--force` ile WB snapshot’larını Player bakiyelerine göre yeniden yazma
- Testler:
  - `backend/tests/test_ops_backfill_wallet_balances.py`

### OPS-02 — Rollout Runbook + Matrix + Secrets Checklist

- Runbook: `docs/payments/ledger-rollout-runbook.md`
- Karar matrisi: `docs/payments/ledger-rollout-matrix.md`
- Secrets checklist: `docs/payments/ledger-rollout-secrets-checklist.md`
- PSP/Ledger tasarım spike’ı: `docs/payments/psp-ledger-spike.md`

---

## 3) Kanıt Komutlar (Backend Full Regression + E2E Smoke)

Aşağıdakiler, RC paketinin test kanıtlarıdır. Ortam isimleri/değerleri staging/prod için uyarlanmalıdır.

### 3.1 Backend Regression (API + Security)

- Hızlı komut (mevcut script):```bash
  cd /app
  python backend_regression_test.py
  ```Özet (mevcut koşumlardan):
  - `/api/health` → 200 OK, `status=healthy`
  - Login rate limit: [401, 401, 401, 401, 401, 429]
  - CORS evil origin istekleri bloklanır (`Access-Control-Allow-Origin: None`)

- Ayrıca:```bash
  cd /app/backend
  pytest -q tests/test_ledger_enforce_balance.py \
         tests/test_ledger_concurrency_c1.py \
         tests/test_psp_mock_adapter.py \
         tests/test_psp_ledger_integration.py \
         tests/test_psp_webhooks.py \
         tests/test_ops_backfill_wallet_balances.py \
         tests/test_psp_reconciliation.py \
         tests/test_psp_reconciliation_api.py \
         tests/test_reconciliation_model.py
  ```### 3.2 E2E Finance Withdrawals Smoke

- Komut (Playwright):```bash
  cd /app/e2e
  yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts
  ```- Kapsam:
  - Player withdraw talebi
  - Admin inceleme/onay
  - Payout/paid olarak işaretleme
  - Ledger snapshot ve UI akışının temel düzeyde doğrulanması

---

## 4) Feature Flag Default'ları (Config)

Referans: `backend/config.py` `Settings` sınıfı

### Ledger / PSP Feature Flag'leri

- `ledger_shadow_write: bool = True`
  - **Dev/local**: True (ledger'a paralel yazım açık)
  - **Staging**: True (OPS-01 backfill + telemetry için zorunlu)
  - **Prod**: True (rollout sonrası da açık kalması önerilir)

- `ledger_enforce_balance: bool = False`
  - Default: False (enforce rollout staging/prod'da kademeli açılır)
  - **Staging**: STG-03 ile full enable (öncesinde STG-01/02 tamamlanmış olmalı)
  - **Prod**: PRD-01/02 ile tenant bazlı ve kademeli enable

- `ledger_balance_mismatch_log: bool = True`
  - Dev/local: True (geliştirme/deney için sorun değil)
  - Staging/prod: True (enforce öncesi/sonrası mismatch metriklerini görmek için)

- `webhook_signature_enforced: bool = False`
  - Default: False (signature enforcement rollout’u STG-02/PRD ile yapılır)
  - Staging: önce OFF → daha sonra ON, 401 spike takibiyle
  - Prod: Pilot tenant’lardan başlayarak ON

### Diğer önemli flag'ler (bazı)

- `allow_test_payment_methods: bool = True`
  - Dev/local: True (test payment method’lar için)
  - Staging/prod: **Politikaya göre güncellenmeli** (tipik olarak False)

---

## 5) Bilinen Notlar & Sınırlamalar

Bu RC, aşağıdaki bilinçli sınırlar ile paketlenmiş durumdadır:

1. **C2 Postgres-Only Concurrency Test Gate**
   - Dosya: `backend/tests/test_ledger_concurrency_c2_postgres.py`
   - Bu test yalnızca **Postgres** için tasarlanmış ve CI (sqlite) ortamında skip edilir.
   - Rollout öncesi staging Postgres ortamında ayrıca çalıştırılıp onaylanmalıdır.

2. **Deprecation Warnings**
   - Bazı Python / SQLAlchemy / Alembic uyarıları runtime'da görülmektedir.
   - Bunlar **RC bloklayıcı değildir** ancak uzun vadede (P1/P2) kütüphane/SDK güncellemeleri ile azaltılmalıdır.

3. **Eski CRM / Tenant Testleri**
   - Bazı eski test setleri (CRM, tenant isolation vs.) RC kapsamının dışında ve bilerek güncellenmemiş durumdadır.
   - Finance/ledger/PSP alanı kapsamı dışında kaldığından, release kararı için bloklayıcı olarak değerlendirilmemiştir.

---

## 6) Sonraki Adımlar (özet)

- **MIG-01**: Alembic chain fix + staging Postgres upgrade/head doğrulaması.
- **STG-ROLL**: Staging rollout (telemetry + OPS-01 backfill + signature enforcement + enforce rollout) — bkz. `ledger-rollout-runbook.md`.
- **PRD-ROLL**: Pilot tenant rollout + kademeli genişletme — bkz. `ledger-rollout-matrix.md` ve secrets checklist.

Bu dosya, RC için PR açıklamasına **doğrudan kopyala-yapıştır** için hazır yapılmıştır.