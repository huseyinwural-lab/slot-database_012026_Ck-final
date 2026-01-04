# 🔴 Ops/Infra CHECKLIST – PSP-03D RC Kapanış (Paket-0/1/2/3)

**Yetki/Sınır:** Bu checklist, RC kapanışı için gerekli kanıt paketlerini (Paket-0/1/2/3) üretmek içindir. Bu doküman “rehberlik” değil **“uygulama talimatı”**dır. Buradaki adımlar tamamlanmadan ilgili ticket **kapanmayacaktır**.

> **Kanut standardı (mutlaka):**
>
> - Her adım için **komut + tam stdout/stderr** ticket’a *metin* olarak eklenecek.
> - Şifre/token maskelenebilir; run_id ve timestamp korunmalı.
> - Her paket sonunda: **PASS/FAIL + 1 cümle not** yazılacak.

---

## Paket-0 — CI Postgres job (zorunlu)

**Paket-0 Minimum Kanıt**

- Job sonucu (GREEN/RED) + job linki
- RED ise en üst hata bloğu

**Aksiyon**

1. GitHub Actions’ta **Backend PSP-03D Postgres Tests** workflow’unu çalıştırın (PR veya `workflow_dispatch`).
2. Ticket’a ekleyin:
   - Job sonucu: **GREEN/RED**
   - Job linki
   - RED ise: en üst hata bloğu + ilgili log bölümü

**PASS kriteri**

- Job **GREEN**.

---

## Paket-1 — STG-MIG (MIG-01B/C) kanıt paketi (zorunlu)

**Paket-1 Minimum Kanıt**

- `alembic current` çıktısı
- `alembic history | tail -n 30` çıktısı
- `alembic upgrade head` tam çıktısı
- `psql \\d reconciliation_findings` çıktısı
- UNIQUE constraint query çıktısı

**Aksiyon (staging backend pod/VM)**

```bash
cd /app/backend || cd backend

alembic current
alembic history | tail -n 30
alembic upgrade head
```

**Aksiyon (staging Postgres / psql)**

```sql
\d reconciliation_findings;

SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'reconciliation_findings'::regclass
  AND contype = 'u';
```

**Opsiyonel smoke (tercihen)**

```bash
cd /app/backend || cd backend
alembic downgrade -1
alembic upgrade head
```

**PASS kriteri**

- `alembic upgrade head` **hatasız**.
- `reconciliation_findings` **tablosu var**.
- `(provider, provider_event_id, finding_type)` için **UNIQUE constraint var**.

**FAIL notu**

- Staging’de `table already exists` vb. çıkarsa: **PASS verilmeyecek**, reset/stamp kararı ticket’a yazılacak.

---

## Paket-2 — STG-ROLL (zorunlu)

**Paket-2 Minimum Kanıt**

- Flag’lerin set edildiğini gösteren kanıt (metin/log)
- Backfill dry-run stdout
- Backfill real-run stdout
- E2E withdrawals smoke PASS log
- 401 spike var/yok kanıtı

**Aksiyon (staging)**

1. **Feature flag’ler:**

   - `ledger_shadow_write=True`
   - `ledger_balance_mismatch_log=True`
   - `webhook_signature_enforced=True`
   - `ledger_enforce_balance=True`

2. **Backfill:**

   ```bash
   python -m backend.scripts.backfill_wallet_balances --dry-run --batch-size 1000
   python -m backend.scripts.backfill_wallet_balances --batch-size 1000
   ```

   - stdout içinden **processed/updated/skipped** sayılarını not edin.

3. **E2E withdrawals smoke:**

   ```bash
   cd /app/e2e
   yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts
   ```

4. **Webhook 401 kontrol:**

   - `WEBHOOK_SIGNATURE_INVALID` için **401 spike var mı?**  
     → (var / yok + kısa kanıt)

**PASS kriteri**

- Backfill **dry-run + real OK**.
- E2E **PASS**.
- 401 spike **yok / normal**.

---

## Paket-3 — PSP-03D Queue enablement (zorunlu)

**Paket-3 Minimum Kanıt**

- Redis healthcheck çıktısı
- Worker start log ilk 20 satır
- POST `reconciliation/runs` response (run_id)
- Worker log (aynı run_id ile started + completed/failed)
- GET run response (lifecycle)

### 3.1 Infra: Redis + Worker

**Aksiyon**

- Redis servisi + **healthcheck**.
- Worker servisi:

  ```bash
  arq app.queue.reconciliation_worker.WorkerSettings
  ```

- **Env (worker):**

  - `DATABASE_URL` (staging)
  - `REDIS_URL`
  - `ENV=staging`

- **Backend env:**

  - `RECON_RUNNER=queue`
  - `REDIS_URL` (worker ile aynı)

- Ticket’a ek: **worker start log ilk 20 satır** (Redis bağlantısı dahil).

### 3.2 Queue path kanıtı (tek run yeterli)

1. `POST /api/v1/reconciliation/runs`
   - Response: `status="queued"` + `id` (**run_id**)
2. Worker log
   - Aynı **run_id** için `started` + `completed/failed`
3. `GET /api/v1/reconciliation/runs/{run_id}`
   - Lifecycle: `queued → running → completed/failed`

**PASS kriteri**

- En az 1 run için lifecycle **run_id ile kanıtlandı** (API + worker log).

---

## Kapanış kuralı

Bu ticket, **Paket-0/1/2/3 PASS olmadan kapanmayacak.**

Herhangi bir paket **FAIL** ise:

- FAIL + tam log ticket’a eklenecek;
- **RCA** Dev/Backend tarafından **aynı ticket** üzerinden yapılacak.
