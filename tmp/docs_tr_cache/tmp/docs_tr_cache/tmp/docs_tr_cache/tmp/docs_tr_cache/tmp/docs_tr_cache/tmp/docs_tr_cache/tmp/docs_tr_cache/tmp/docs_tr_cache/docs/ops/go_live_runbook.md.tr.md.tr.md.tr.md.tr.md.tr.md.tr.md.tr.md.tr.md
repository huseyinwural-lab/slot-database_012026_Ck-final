# Go-Live Cutover Runbook & RC Onayı

## Cutover Önkoşulları
**Bunlar sağlanmadan cutover başlatmayın:**
*   **Release Sabitleme:** Release SHA/Tag sabitlendi ve paylaşıldı.
*   **Erişim:** Sorumlu sahipler için Prod erişimi (DB, Registry, Deploy) doğrulandı.
*   **Artefaktlar:** RC Artefaktları (`/app/artifacts/rc-proof/`) mevcut ve hash’ler doğrulandı.
*   **Rollback:** Plan ve "Restore Point" (Snapshot) sahibi atandı.
*   **Canary:** Canary kullanıcı/tenant hazır, test tutarları tanımlandı.
*   **Hypercare:** On-call rotasyonu ve alarm kanalları aktif.

## War Room Protokolü (Sprint 7 Cutover)
**Amaç:** GO/NO-GO kararları için tek doğruluk kaynağı.

### Roller
*   **Incident Commander (IC):** Tek karar verici (GO/NO-GO/ROLLBACK).
*   **Deployer:** Deploy ve smoke script’lerini çalıştırır.
*   **DB Owner:** Snapshot’ları ve migration izlemeyi yönetir.
*   **Payments Owner:** Canary Money Loop & Ledger Invariants doğrular.
*   **Scribe:** Zaman çizelgesini, referansları ve kararları kaydeder.

### Kurallar
1.  Tüm adımlar checklist’e göre ilerler. Atlamak yok.
2.  **Canary FAIL = NO-GO** (İstisna yok).
3.  Rollback tetikleyicisi gözlenirse IC 5 dakika içinde karar verir.
4.  Her adımı logla: PASS/FAIL + Zaman damgası.

### Zaman Çizelgesi (Scribe Formatı)
*   **T-60:** Pre-flight Başlangıç/Bitiş.
*   **T-30:** Snapshot ID kaydedildi.
*   **T-15:** Deploy Başlangıç/Bitiş.
*   **T-10:** Smoke PASS/FAIL.
*   **T-0:** Canary PASS/FAIL.
*   **T+15:** GO/NO-GO Kararı.
*   **T+60:** İlk Hypercare Raporu.

## İletişim Planı (Cutover Duyurusu)
### Kanallar & Mesajlar
1.  **Cutover Başlangıcı:** "Cutover başlatıldı. Bakım penceresi aktif. Her 15 dakikada bir güncelleme."
2.  **Kontrol Noktası Güncellemeleri:**
    *   "Pre-flight PASS"
    *   "Backup PASS"
    *   "Deploy+Smoke PASS/FAIL"
    *   "Canary PASS/FAIL"
3.  **GO-LIVE Duyurusu:** "GO kararı verildi. Sistem canlı. Hypercare başladı."
4.  **Rollback (Gerekirse):** "Rollback tetiklendi. Sebep: [X]. Geri yükleme devam ediyor."

### Güncelleme Sıklığı
*   **Cutover Sırasında:** Her 15 dakikada bir veya kontrol noktalarında.
*   **İlk 2 Saat:** Her 30 dakikada bir.
*   **2-24 Saat:** Saatlik özet.

---

## 1. RC Onay Kriterleri (Sağlandı)
- **E2E (Money Loop):** PASS (Polling ile deterministik).
- **Backend Regression:** PASS (8/8 test, ledger invariants kapsar).
- **Router/API:** `payouts` router’ının aktif olduğu doğrulandı.
- **Ledger Logic:** Payout’ta bakiye düşümü doğrulandı.
- **Artefaktlar:** `/app/artifacts/rc-proof/` içinde doğrulandı ve hash’lendi.

## 2. Go-Live Cutover Runbook (T-0 Uygulaması)

### A) Cutover Öncesi (T-60 -> T-0)
1.  **Release Freeze:** 
    - Main branch kilitlendi.
    - RC Tag/Commit SHA doğrulandı.
2.  **Prod Config Doğrulaması:**
    - PSP Keys (Stripe/Adyen Live)
    - Webhook Secrets
    - DB URL & Trusted Proxies
    - `BOOTSTRAP_ENABLED=false`
3.  **DB Backup:**
    - Snapshot alındı (Restore test edildi).
4.  **Migration Kontrolü:**
    - Mümkünse prod kopyası üzerinde dry-run `alembic upgrade head`.

### B) Cutover (T-0)
1.  **Maintenance Mode:**
    - Maintenance Page etkinleştir / Ingress’i engelle.
2.  **Deploy:**
    - Docker image’larını çek.
    - `docker-compose up -d` (veya k8s apply).
3.  **Migrations:**
    - `alembic upgrade head` çalıştır.
4.  **Health Check:**
    - `/api/health` doğrula.
    - Admin girişini kontrol et.
    - Dashboard yüklenmesini kontrol et.
    - Trafiği aç.

### Araçlar & Script’ler
- **Config Doğrulaması:** `python3 scripts/verify_prod_env.py`
- **Backup Drill:** `bash scripts/db_restore_drill.sh`
- **Smoke Test:** `bash scripts/go_live_smoke.sh`

### C) Cutover Sonrası (T+0 -> T+30)
1.  **Canary Smoke Test:**
    - Gerçek para ile Deposit ($10).
    - Gerçek para ile Withdraw ($10).
    - **Rapor Şablonu:** Yapılandırılmış onay için `docs/ops/canary_report_template.md` kullanın.
2.  **Ledger Kontrolü:**
    - `held` -> `0` ve `available` değerinin doğru şekilde azaldığını doğrula.
3.  **Webhook İzleme:**
    - `Signature Verified` event’leri için log’ları tail et.
4.  **Error Budget:**
    - 5xx sıçramaları için Sentry/Logs izle.

## 3. Rollback Planı
**Tetikleyiciler:**
- Payout Failure Rate > %15.
- Kritik Güvenlik Olayı.
- Ledger Invariant İhlali.

**Adımlar:**
1.  Maintenance Mode’u etkinleştir.
2.  Önceki Docker Tag / Commit’e dön.
3.  DB Snapshot’ını geri yükle (veri bozulması şüphesi varsa) VEYA Migration’ı geri al (güvenliyse).
4.  Login & Read-Only endpoint’lerini doğrula.
5.  Trafiği yeniden aç.

## 4. Sprint 7 — Cutover Komut Sayfası (Tek Sayfa)

### T-60 — Pre-flight
1.  **Release Sabitleme:** `RELEASE_SHA` / Tag tanımla.
2.  **Prod Env Kontrolü:** `python3 scripts/verify_prod_env.py`
    *   *Kabul Kriteri:* Prod modu, CORS kısıtlı, test secret’ları yok (veya ticket ile muafiyet verilmiş).

### T-30 — Backup
1.  **DB Snapshot:** Cloud Provider üzerinden veya `pg_dump` ile çalıştır (Prod’da restore drill çalıştırmayın).
2.  **Kayıt:** Snapshot ID/Path + Zaman damgası + Checksum.

### T-15 — Deploy + Migration + Smoke
1.  **Deploy & Migrate:** `bash scripts/go_live_smoke.sh`
    *   *Kabul Kriteri:* Migrations OK, API Health 200, Login OK, Payouts Router erişilebilir.

### T-0 — Canary Money Loop (GO Kararı)
1.  **Çalıştır:** `docs/ops/canary_report_template.md` adımları.
    *   Deposit -> Withdraw Request -> Admin Approve -> Mark Paid -> Ledger Settlement.
2.  **Karar:**
    *   ✅ **GO:** Canary PASS + Artefaktlar güvence altına alındı.
    *   ❌ **NO-GO (Rollback):** Canary FAIL.

### Rollback Karar Matrisi
| Tetikleyici | Aksiyon |
| :--- | :--- |
| Payout/Withdraw 404/5xx | **Hemen Rollback** |
| Migration Failure | **Hemen Rollback** |
| Ledger Invariant Breach | **Hemen Rollback** |
| Webhook Misclassification | **Hemen Rollback** |
| Latency Spike (Hata Yok) | İzle (Hypercare) |
| Queue Backlog (< SLA) | İzle (Hypercare) |

### 6) Hypercare Araçları & Script’ler
- **Stuck Job Detector:** `python3 scripts/detect_stuck_finance_jobs.py` (Her 30 dakikada bir çalıştır)
- **Daily Recon Report:** `python3 scripts/daily_reconciliation_report.py` (Günlük çalıştır)
- **Waiver Tracking:** `artifacts/prod_env_waiver_register.md`

### Hypercare Rutini (72s)
*   **0-6s:** Her 30 dakikada bir kontrol.
*   **6-24s:** Saatlik kontrol.
*   **24-72s:** Günde 3 kez kontrol.
*   **Odak:** 5xx oranları, Queue Backlog, Webhook Hataları, Rastgele Ledger Recon.

## 5. Sprint 7 — Uygulama Checklist’i (Onay)

### 1) Pre-flight (T-60)
- [ ] Release SHA/Tag sabitlendi: __________________
- [ ] Sorumlular atandı (Deploy / DB / On-call): __________________
- [ ] `verify_prod_env.py` çalıştırıldı -> Sonuç: PASS / FAIL
    - Log ref: __________________

### 2) Backup (T-30)
- [ ] Prod DB snapshot alındı -> Snapshot ID/Path: __________________
- [ ] Snapshot erişilebilirliği doğrulandı -> PASS / FAIL
- [ ] Rollback restore prosedürü erişilebilir -> PASS / FAIL

### 3) Deploy + Migration + Smoke (T-15)
- [ ] Deploy tamamlandı -> PASS / FAIL
- [ ] `go_live_smoke.sh` çalıştırıldı -> PASS / FAIL
    - [ ] API health 200 -> PASS / FAIL
    - [ ] Admin login -> PASS / FAIL
    - [ ] Payouts router erişilebilir -> PASS / FAIL
    - Log ref: __________________

### 4) Canary Money Loop (T-0) — GO/NO-GO
- [ ] Deposit -> PASS / FAIL (Tx ID: __________________)
- [ ] Withdraw isteği -> PASS / FAIL (ID: __________________)
- [ ] Admin onayı -> PASS / FAIL (Timestamp: __________________)
- [ ] Admin ödendi olarak işaretleme -> PASS / FAIL (Timestamp: __________________)
- [ ] Ledger settlement / invariant -> PASS / FAIL (Refs: __________________)
- [ ] Canary raporu tamamlandı (`docs/ops/canary_report_template.md`) -> PASS / FAIL

**GO/NO-GO Kararı:** GO / NO-GO  
**Karar Veren:** __________________ **Tarih/Saat:** __________________

### 5) Hypercare (T+0 -> T+72h)
- [ ] Alarm mekanizması aktif (5xx/latency/DB/webhook) -> PASS / FAIL
- [ ] İlk 6 saatlik izleme periyodu uygulandı -> PASS / FAIL
- [ ] 24 saat kontrol raporu -> PASS / FAIL
- [ ] 72 saat stabil -> PASS / FAIL

---
**Canary "GO" Karar Beyanı (Standart)**
"Prod deploy smoke kontrolleri PASS. Canary Money Loop (deposit->withdraw->approve->paid->ledger settlement) PASS. Rollback tetikleyicisi gözlenmedi. GO-LIVE teyit edildi."

## Go-Live Tamamlama Kriterleri
**Go-Live aşağıdaki durumlarda "TAMAMLANDI" kabul edilir:**
*   Smoke Testleri (Health, Auth, Payouts) **PASS**.
*   Canary Money Loop **PASS** ve rapor kayda alındı.
*   İlk 2 saatte 5xx sıçraması yok (normal baseline).
*   Withdraw/Payout Queue kontrol altında (SLA ihlali yok).
*   Rollback tetikleyicisi gözlenmedi.
*   24 saat kontrol raporu yayınlandı (Özet + Metrikler + Aksiyonlar).