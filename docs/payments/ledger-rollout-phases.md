# Ledger Rollout Phases (STG-MIG → STG-ROLL → PRD-PILOT → PRD-GA)

Bu doküman RC kapanışı için tek gerçek “runbook checklist”tir.
Dev/local (SQLite) hataları (örn. "table already exists") staging/prod Postgres için referans değildir.

## Faz 1 — STG-MIG (P0) — MIG-01B/C staging Postgres doğrulama

### 1.1 Doğru DB’ye bağlandığını kanıtla (Postgres + Alembic aynı DB’yi görmeli)
Staging pod/VM içinde:

```bash
cd /app/backend || cd backend

# DB URL (maskeli): host/DB doğrulaması için
python -c "import os; u=os.getenv('DATABASE_URL',''); print(u.split('@')[-1] if '@' in u else u)"

alembic current
alembic history | tail -n 30
Beklenen:
•	alembic current boş değil.
•	History zinciri:
abcd1234_ledgertables -> 20251222_01_reconciliation_findings -> 20251222_02_reconciliation_findings_unique_idx (head)
1.2 Upgrade head (asıl kanıt)
Bash:
cd /app/backend || cd backend
alembic upgrade head
Beklenen: Hatasız bitmesi.
Not:
•	Eğer staging’de de table already exists görülürse, tablo Alembic dışında oluşturulmuş olabilir ve alembic_version geride kalmıştır.
•	Prod’a dokunmadan önce sadece staging’de iki seçenek:
1.	Tercih edilen: staging DB reset + temiz alembic upgrade head
2.	Alternatif: çok kontrollü alembic stamp <rev> + upgrade head
1.3 Postgres’te tablo + unique constraint doğrulaması
psql ile:
sql:
\d reconciliation_findings;

SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'reconciliation_findings'::regclass
  AND contype = 'u';
Beklenen:
•	tablo var
•	UNIQUE: (provider, provider_event_id, finding_type) (örn. uq_recon_provider_event_type)
1.4 (Önerilir) ileri/geri smoke (sadece staging)
Bash:
cd /app/backend || cd backend
alembic downgrade -1
alembic upgrade head
DoD (Faz 1):
•	alembic current head’de
•	upgrade head hatasız
•	constraint doğrulanmış
•	(tercihen) downgrade/upgrade smoke hatasız
Faz 2 — STG-ROLL (P0) — Staging rollout
Amaç: runbook’taki bayrakları sırayla açıp akış stabilitesini doğrulamak.
2.1 Telemetry + shadow-write
•	ledger_shadow_write=True
•	ledger_balance_mismatch_log=True
2.2 OPS-01 backfill (staging)
Bash:
python -m backend.scripts.backfill_wallet_balances --dry-run --batch-size 1000
python -m backend.scripts.backfill_wallet_balances --batch-size 1000
2.3 Webhook signature enforcement (kademeli)
•	webhook_signature_enforced=True
İzleme: 401 WEBHOOK_SIGNATURE_INVALID artışı var mı?
2.4 Enforce balance aç + E2E withdrawals smoke
•	ledger_enforce_balance=True
bash:
cd /app/e2e
yarn test:e2e -- tests/finance-withdrawals-smoke.spec.ts
DoD (Faz 2):
•	Enforce açıkken deposit/withdraw/admin approve/mark-paid akışı stabil.
Faz 3 — PRD-PILOT (P0) — Prod pilot rollout
3.1 Pilot tenant seçimi
•	1–3 düşük riskli tenant
3.2 Pilot backfill + signature + enforce
•	tenant-scoped backfill (OPS-01)
•	webhook_signature_enforced=True (pilot)
•	ledger_enforce_balance=True (pilot)
3.3 İzleme ve karar matrisi (OPS-02)
Eşikler:
•	400 INSUFFICIENT_FUNDS artışı
•	webhook 401 artışı
•	mismatch spike
DoD (Faz 3):
•	Pilot stabil → genişleme onayı
Faz 4 — PRD-GA (P0) — Kademeli genişleme
•	Tenant bazında rollout genişlet
•	Gerekirse tenant-scoped backfill tekrarları
•	Rollback prosedürü hazır (OPS-02)
DoD (Faz 4):
•	Genel kullanımda enforce açık, operasyonel olarak sürdürülebilir.

Bu dokümanın “tek sayfa” olmasının nedeni şu: staging’de komutları çalıştıran kişi **karar vermesin**, sadece uygulasın. RC bu şekilde kapanır.
