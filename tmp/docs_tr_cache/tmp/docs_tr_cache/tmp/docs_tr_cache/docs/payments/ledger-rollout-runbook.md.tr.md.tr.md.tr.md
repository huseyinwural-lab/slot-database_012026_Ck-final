# Ledger Enforce Rollout Runbook

## 1. Amaç & Kapsam

Bu runbook, **ledger_enforce_balance** ve ilgili PSP/webhook güvenlik ayarlarının
staging ve production ortamlarında güvenli bir şekilde devreye alınması için
izlenecek adımları tanımlar.

Hedefler:
- Player bakiyesi için **WalletBalance**'ı tek hakem yapmak (LEDGER-02B).
- Enforce açılmadan önce **OPS-01 backfill** ile tüm wallet_balances snapshot'larını
doldurmak.
- Webhook'lar için imza doğrulamasını (MockPSP dahil) kademeli olarak devreye
  almak.
- Geri dönüş (rollback) için net ve test edilmiş bir prosedür sağlamak.

Kapsam:
- Backend feature flag'leri:
  - `ledger_shadow_write`
  - `ledger_enforce_balance`
  - `ledger_balance_mismatch_log`
  - `webhook_signature_enforced`
- OPS-01 backfill script'i:
  - `python -m backend.scripts.backfill_wallet_balances ...`
- PSP-01/02 entegrasyonları (MockPSP + webhook)
- PSP-03D: reconciliation run endpoint + runs tablosu (PSP reconciliation operability)

---

## 2. Ön Koşullar

Rollout'a başlamadan önce aşağıdaki maddelerin sağlandığından emin olun:

1. **Migration'lar uygulanmış olmalı**
   - `ledger_transactions` ve `wallet_balances` tabloları mevcut.
   - Gerekli unique indexler (özellikle `(provider, provider_event_id)` ve
     `(tenant_id, player_id, type, idempotency_key)`) deploy edilmiş.

2. **OPS-01 backfill script'i hazır ve test edilmiş olmalı**
   - Testler:
     - `pytest -q tests/test_ops_backfill_wallet_balances.py`
   - Script:
     - `backend/scripts/backfill_wallet_balances.py`

3. **Webhook/PSP konfigurasyonu çalışır durumda olmalı**
   - `webhook_secret_mockpsp` env'de düzgün set edilebilir.
   - `/api/v1/payments/webhook/mockpsp` endpoint'i **PSP-02 testleri** ile
     doğrulanmış olmalı:
     - `pytest -q tests/test_psp_webhooks.py`

4. **Temel regresyon seti temiz olmalı**
   - `pytest -q tests/test_ledger_repo.py tests/test_ledger_shadow_flows.py tests/test_ledger_enforce_balance.py tests/test_ledger_concurrency_c1.py tests/test_psp_mock_adapter.py tests/test_psp_ledger_integration.py tests/test_psp_webhooks.py tests/test_ops_backfill_wallet_balances.py`
   - `cd /app/e2e && yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts`

---

## 3. Telemetry Açma (ledger_balance_mismatch_log)

Amaç: Enforce açılmadan önce legacy Player bakiyesi ile WalletBalance snapshot'ı
arasındaki farkları ölçmek.

### 3.1 Flag ayarı

- Config: `backend/config.py` içindeki `Settings` sınıfı:
  - `ledger_balance_mismatch_log: bool = True`

Prod/staging için **önerilen default**: `True`.

### 3.2 Telemetry sinyalinin anlamı

- Kod: `app/services/ledger_telemetry.py` → `record_balance_mismatch(...)`
- Ne zaman çağrılır?
  - Withdraw flow'da, ledger snapshot ile Player.available uyuşmazsa.
- Nasıl gözlemlenir?
  - Şu an global bir counter (`mismatch_counter`) ve log ekleme için TODO
    notu mevcut.
  - Rollout sırasında aşağıdakiler yapılmalı:
    - `mismatch_counter` metrik olarak expose edilirse: **trende bakın**.
    - Aksi halde, log'larda `record_balance_mismatch` çağrılarının frekansını
      takip edin (ileride structured log pattern'i eklenebilir).

Hedef: Backfill sonrasında mismatch oranının anlamlı şekilde düşmesi.

---

## 4. Backfill Adımları (OPS-01)

Backfill script'i Player → WalletBalance mapping'ini yapar:
- `Player.balance_real_available` → `WalletBalance.balance_real_available`
- `Player.balance_real_held` → `WalletBalance.balance_real_pending`

Komut iskeleti:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000 \
  [--tenant-id <tenant_uuid>] \
  [--dry-run] \
  [--force]
```

### 4.1 Dry-run (zorunlu ilk adım)

Örnek:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000 \
  --dry-run
```

Beklenen davranış:
- DB'ye hiçbir write yapılmaz.
- Log çıktısında özet görünür:
  - `scanned`
  - `created`
  - `skipped_exists`
  - `updated_forced`
  - `errors`

Bu çıktıyı kaydedip (özellikle `created` sayısı) gerçek koşumla
karşılaştırmak için saklayın.

### 4.2 Global backfill (tüm tenant'lar)

Dry-run çıktısı makul ise:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000
```

Notlar:
- Default davranış: **WB varsa skip** (idempotent).
- Büyük tenant'lar için `--batch-size` gerekirse düşürülebilir (örn. 500).

### 4.3 Tenant scoped backfill

Belirli bir tenant için tekrar koşmak istediğinizde:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000 \
  --tenant-id <tenant_uuid>
```

Kullanım senaryoları:
- Yeni onboard edilen tenant'lar.
- Sadece belirli tenant'ta gözlenen mismatch sorunlarını düzeltmek.

### 4.4 Force overwrite (istisnai)

Önceden yanlış backfill yapılmış veya Player bakiyeleri manuel olarak
revize edilmiş ise, WB'leri zorla güncellemek için:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000 \
  --force
```

Öneri:
- `--force` daima **önce dry-run** ile kullanılmalı:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000 \
  --force \
  --dry-run
```

Log çıktısını dikkatle inceleyin (`updated_forced` sayısı) ve ancak ondan sonra
force backfill'i gerçek modda koşun.

---

## 5. Enforce Açma Stratejisi (ledger_enforce_balance)

Amaç: `ledger_enforce_balance=True` ile withdraw funds check'in tamamen
`WalletBalance` üzerinden yapılmasını güvenle devreye almak.

### 5.1 Flag kontrolü

Config:
- `backend/config.py`:
  - `ledger_enforce_balance: bool = False` (default)

Prod rollout için öneri:
- Staging: full enable
- Prod: tenant bazlı/kademeli enable

### 5.2 Önerilen rollout stratejisi

1. **Staging ortamında**
   - `ledger_balance_mismatch_log=True`
   - Backfill (OPS-01) tam koşum
   - `ledger_enforce_balance=True`
   - Staging load test'leri + end-to-end withdraw senaryoları

2. **Prod pilot tenant'lar**
   - Bir pilot tenant listesi belirleyin (yüksek hacimli olmayan ama kritik
     olmayan tenant'lar).
   - Eğer uygulamada tenant bazlı override mekanizması yoksa, rollout'ı
     **zaman penceresi** üzerinden yönetin (ör. önce gece saatleri).
   - Aşağıdaki metrikleri izleyin:
     - 400 `INSUFFICIENT_FUNDS` artışı (anomalik mi?)
     - Webhook 401 (signature) artışı
     - ledger_balance_mismatch trendi

3. **Genel enable**
   - Pilot tenant'larda sorun yoksa `ledger_enforce_balance=True`'yi global
     olarak açın.

Not: Eğer gelecekte tenant bazlı flag (ör. `Tenant.flags.ledger_enforce_override`)
uygulanırsa, bu strateji daha da güvenli hale getirilebilir.

---

## 6. Doğrulama Checklist'i

Enforce'i açtıktan sonra aşağıdaki checklist üzerinden doğrulama yapın:

1. **Mismatch trendi**
   - `ledger_balance_mismatch_log` telemetrisi:
     - Backfill öncesi: mismatch sayısı yüksek olabilir.
     - Backfill sonrası: mismatch belirgin şekilde düşmüş olmalı.

2. **Withdraw success rate**
   - 400 `INSUFFICIENT_FUNDS` hatalarının oranı:
     - Beklenen: Yalnızca gerçekten funds yetersiz olduğunda.
     - Beklenmeyen: Eskiden geçen işlemler şimdi 400 dönüyorsa sorun vardır.

3. **Webhook error oranı**
   - 4xx/5xx oranları `/api/v1/payments/webhook/*` endpoint'lerinde.
   - Signature enforcement ON ise 401 artışlarını yakından takip edin.

4. **E2E smoke / kritik akışlar**
   - `cd /app/e2e && yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts`
   - Admin withdraw lifecycle'ı (player withdraw → admin approve → mark-paid)
     sorunsuz çalışmalı.

---

## 7. Rollback Prosedürü

Aşağıdaki tetikleyicilerden biri gözlenirse rollback düşünülmelidir:

- Beklenmeyen 400 `INSUFFICIENT_FUNDS` artışı.
- Webhook 401 (WEBHOOK_SIGNATURE_INVALID) oranında anlamlı spike.
- ledger_balance_mismatch telemetrisinde ani yükseliş.
- E2E withdraw akışının bozulması.

### 7.1 Rollback adımları

1. **Enforce flag'ini kapatın**

```bash
# Config değişikliği (örn. .env veya deployment config):
LEDGER_ENFORCE_BALANCE=False

# Uygulamayı yeniden deploy / restart edin.
```

2. **Gerekirse webhook imza enforcement'ı kapatın**

Özellikle gerçek PSP entegrasyonunda yanlış/eksik secret kaynaklı 401 fırtınası
jenerik bir issue ise:

```bash
WEBHOOK_SIGNATURE_ENFORCED=False
```

3. **Log ve metrikleri yeniden değerlendirin**

- Enforce OFF sonrası error oranlarının normale dönüp dönmediğini kontrol edin.
- Gerekirse yeni backfill (OPS-01) dry-run + run adımlarını tekrar edin.

4. **E2E smoke tekrar**

Rollback sonrası:

```bash
cd /app/backend
pytest -q tests/test_ops_backfill_wallet_balances.py

cd /app/e2e
yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts
```

---

## 8. Reconciliation (PSP-03) İşletimi

Reconciliation, PSP ile ledger arasındaki farkları tespit etmek için
periyodik veya isteğe bağlı olarak çalıştırılır.

### 8.1 Reconciliation job'ı tetiklemek (admin endpoint)

Staging/prod ortamında, admin-only endpoint üzerinden reconcile tetiklenebilir:

```bash
cd /app/backend
# Varsayılan provider: mockpsp, tenant scope: current tenant
curl -X POST \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  /api/v1/payments/reconciliation/run
```

Belirli bir tenant için manuel tetikleme:

```bash
curl -X POST \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"provider": "mockpsp", "tenant_id": "<tenant_uuid>"}' \
  /api/v1/payments/reconciliation/run
```

### 8.2 Findings okuma ve aksiyon alma

1. **Findings listesini çekin**

```bash
curl -X GET \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  "/api/v1/payments/reconciliation/findings?provider=mockpsp&status=OPEN&limit=50&offset=0"
```

Dönüşte göreceğiniz tipler:
- `missing_in_ledger`
- `missing_in_psp`

2. **Örnek aksiyonlar**

- `missing_in_ledger`:
  - PSP'de görünen event için ledger tarafında neden event olmadığı incelenir
    (webhook log'ları, append_event hataları vb.).
  - Gerekirse ilgili tx için manuel ledger düzeltmesi yapılır.

- `missing_in_psp`:
  - Ledger'da görünen event için PSP portal/raporları kontrol edilir.
  - Gerçek para hareketi yoksa ledger event'i veya snapshot düzeltmesi gerekir.

3. **Finding resolve akışı**

İncelenip aksiyon alınmış bulguları `RESOLVED` işaretlemek için:

```bash
curl -X POST \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  /api/v1/payments/reconciliation/findings/<finding_id>/resolve
```

Bu, future run'larda aynı bulguyu tekrar tekrar manuel gözden geçirmenizi
engeller; yalnızca yeni bulgulara odaklanmanızı sağlar.

---

## 9. Komut Örnekleri (Kopyala-Çalıştır)

### 8.1 Backfill dry-run (tüm tenant'lar)

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances --batch-size 1000 --dry-run
```

### 8.2 Backfill gerçek koşum (tüm tenant'lar)

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances --batch-size 1000
```

### 8.3 Tenant scoped backfill

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --tenant-id <tenant_uuid> \
  --batch-size 1000
```

### 8.4 Force overwrite (önce dry-run, sonra gerçek)

Dry-run:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000 \
  --force \
  --dry-run
```

Gerçek koşum:

```bash
cd /app/backend
python -m backend.scripts.backfill_wallet_balances \
  --batch-size 1000 \
  --force
```

### 8.5 Regresyon testi (backend)

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

### 8.6 E2E smoke (withdrawals)

```bash
cd /app/e2e
yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts
```
