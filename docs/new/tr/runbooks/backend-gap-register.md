# Backend Gap Register (TR)

**Son gözden geçirme:** 2026-01-05  
**Sorumlu:** Platform Engineering / Ops  

Bu register, Admin Panel dokümantasyonu sırasında tespit edilen **UI ↔ Backend uyumsuzluklarını** tek bir yerde toplar.

**Nasıl kullanılır?**
- Her kayıt **kapatılabilir** olmalıdır (owner + SLA + doğrulama).
- EN/TR dosyaları birebir mirrored tutulmalıdır (bkz: `/docs/new/en/runbooks/backend-gap-register.md`).
- Status akışı: **Open → In Progress → Fixed → Verified**.

---

## Triage Summary (Ops)

| ID | Alan | Gap | Öncelik | Owner | SLA | Target Version | Status | Workaround | Doğrulama |
|---:|------|-----|---------|-------|-----|---------------|--------|------------|----------|
| G-001 | Games | Import 404 dönüyor | P1 | Backend | 7d | TBD | Verified | N/A | Endpoint 200 döner; UI import başarılı |
| G-002 | System → API Keys | Toggle/patch 404 dönüyor | P1 | Backend | 7d | TBD | Verified | N/A | Patch 200; UI toggle persist |
| G-003 | Reports / Simulator | Reports endpoint’leri ve simulator koşuları stub/404 | P1 | Backend | 7d | TBD | Verified | N/A | Report endpoint’leri data döner; simulator run endpoint’leri var |

> SLA default: P0=24h, P1=7d, P2=30d.

---


> Bu register, menü sayfalarındaki “Backend/Integration Gap’leri” bölümlerini tamamlar.
> Bir gap doğrulandığında, aksiyon takibi için buraya ekleyin.

## 1) Açık gap’ler (modül bazlı)

### 1.1 Core → Games → Manual import endpoint’leri 404 dönüyor

- **ID:** G-001
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** High

#### Verification contract

**API contract (geçmeli):**
1) `POST /api/v1/game-import/manual/upload`
   - Request: UI’ın kullandığı şekilde `multipart/form-data` (file field)
   - Beklenen: **200 OK**
   - Response: `job_id` (string) içeren JSON

2) `GET /api/v1/game-import/jobs/{job_id}`
   - Beklenen: **200 OK**
   - Response: en az `{ job_id, status }` (status ∈ `queued|running|ready|failed|completed` veya eşdeğeri)

3) `POST /api/v1/game-import/jobs/{job_id}/import`
   - Beklenen: **200 OK**
   - Response: `imported_count` (number) + `status` (örn. `completed`)

**UI doğrulama (geçmeli):**
- Admin UI: Core → Games → Import akışı 404 olmadan tamamlanır ve success toast/state görünür.

**“Verified” kanıtı:**
- DevTools Network’te yukarıdaki 3 endpoint’in 200 döndüğünü gösteren ekran görüntüsü.

- **Kaynak sayfa:** `/docs/new/tr/admin/core/games.md`
- **Belirti:** Game manual upload / preview / confirm import akışı **404 Not Found** ile fail ediyor.
- **UI endpoint’leri:**
  - `POST /api/v1/game-import/manual/upload`
  - `GET /api/v1/game-import/jobs/{job_id}`
  - `POST /api/v1/game-import/jobs/{job_id}/import`
- **Etki:** Katalog ingestion/import bu ortamda bloklanır.
- **Admin workaround:** Yok; backend bu route’ları destekleyene kadar import’u erteleyin.
- **Escalation paketi:**
  - Yukarıdaki endpoint’ler için DevTools Network’ten 404 kanıtı
  - Beklenen vs gerçek: 200 + `{ job_id }` vs 404
  - Anahtar kelimeler: `game-import`, `import`
- **Doğrulama (fix sonrası):** Upload 200 + `job_id`; job fetch 200; confirm import 200; UI akışı tamamlar.

---

### 1.2 System → API Keys → Toggle endpoint’i 404 dönüyor

- **ID:** G-002
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Verified / Closed
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** High

**Kapanış notu:** G-002 (API Keys toggle): PATCH implement edildi, tenant isolation enforced, test PASS. Status: Verified / Closed.

#### Verification contract

**API contract (geçmeli):**
1) `GET /api/v1/api-keys/`
   - Beklenen: **200 OK**
   - Response: key listesi (array); her item en az `{ id, name, scopes, active }`

2) `PATCH /api/v1/api-keys/{id}`
   - Request body: `{ "active": true|false }`
   - Beklenen: **200 OK**
   - Response: güncellenmiş key objesi (`active` yeni state’i yansıtır)

3) (Opsiyonel ama önerilir) `GET /api/v1/api-keys/scopes`
   - Beklenen: **200 OK**
   - Response: scope listesi (array)

**UI doğrulama (geçmeli):**
- Admin UI: System → API Keys (veya Settings → API Keys) toggle ile key aktif/pasif yapılır.
- Sayfa refresh sonrası state korunur.

**“Verified” kanıtı:**
- DevTools Network’te `PATCH /api/v1/api-keys/{id}` = 200 ve ardından list refresh’te `active` alanının güncellendiği görülür.

- **Kaynak sayfa:** `/docs/new/tr/admin/system/api-keys.md`
- **Belirti:** Key status toggle işlemi **404 Not Found** dönüyor.
- **UI endpoint’i:** `PATCH /api/v1/api-keys/{id}` body `{ active: true|false }`
- **Etki:** Key disable/enable güvenli şekilde yapılamaz; incident response ve rotate prosedürü zayıflar.
- **Admin workaround:** Key’leri statik kabul edin; yeni key üretip eskiyi secret manager tarafında revoke edin (varsa).
- **Escalation paketi:**
  - `PATCH /api/v1/api-keys/{id}` için DevTools Network 404 kanıtı
  - Beklenen vs gerçek: 200 vs 404
  - Anahtar kelimeler: `api-keys`, `PATCH`
- **Doğrulama (fix sonrası):** Patch 200; UI toggle değişimi görünür; refresh sonrası state persist.

---

### 1.3 System → Reports / Simulator → Endpoint’ler stub veya eksik

- **ID:** G-003
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Verified / Closed
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** Medium

**Kapanış notu:** G-003 (Reports/SimulationLab): MVP endpoint’ler implement edildi, stub kalktı, tenant isolation enforced, test PASS (8/8). Status: Verified / Closed.

#### Verification contract

**API contract (geçmeli, minimum):**
1) Reports
   - `GET /api/v1/reports/overview` → **200 OK** (UI render edebileceği non-empty JSON object/array)
   - `POST /api/v1/reports/exports` body `{ type, requested_by }` → **200 OK** (export job referansı: `{ id }` veya `{ job_id }`)
   - `GET /api/v1/reports/exports` → **200 OK** (yeni job’u içeren array)

2) Simulator (Simulation Lab)
   - `GET /api/v1/simulation-lab/runs` → **200 OK** (array; başlangıçta boş olabilir)

**UI doğrulama (geçmeli):**
- Reports (`/reports`): Overview 404 olmadan yüklenir ve içerik render eder.
- Export: export job oluşturulur ve Export Center’da görünür.
- Simulator (`/simulator`): runs listesi 404 olmadan yüklenir.

**“Verified” kanıtı:**
- DevTools Network:
  - `GET /api/v1/reports/overview` = 200
  - `POST /api/v1/reports/exports` = 200
  - `GET /api/v1/simulation-lab/runs` = 200

- **Kaynak sayfalar:**
  - `/docs/new/tr/admin/system/reports.md`
  - `/docs/new/tr/admin/system/simulator.md`
- **Belirti:** Reports sayfaları empty/stub data veya 404 döner; simulator aksiyonları run oluşturmuyor.
- **Muhtemel neden:** `/api/v1/reports/*` ve simulator run endpoint’leri bu build’de tam implement değil.
- **UI endpoint’leri (örnek):**
  - `GET /api/v1/reports/overview` (ve diğer tab’ler)
  - `POST /api/v1/reports/exports`
  - (simulator) run endpoint’leri modüle göre değişir
- **Admin workaround:** Export-only varsa kullanın; yoksa DB/log üzerinden manuel analiz.
- **Escalation paketi:**
  - DevTools Network’ten ilk fail eden path(ler)
  - Beklenen vs gerçek: 200 + data vs 404/empty
  - Anahtar kelimeler: `reports`, `exports`, `simulator`
- **Doğrulama (fix sonrası):** Report endpoint’leri anlamlı data döner; export job 200; simulator run’ları oluşturulur ve listelenir.

---


### 1.4 System → Logs → Kategori endpoint’leri boş liste dönüyor

- **ID:** G-004
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** Medium

- **Kaynak sayfa:** `/docs/new/tr/admin/system/logs.md`
- **Belirti:** Çoğu tab `[]` dönüyor / “No logs found” gösteriyor (bilinen incident sırasında bile).
- **Muhtemel neden:** `backend/app/routes/logs.py` içinde `/events` var; ancak birçok kategori endpoint’i stub veya boş liste dönüyor.
- **Etki:** Ops Logs UI’dan kanıt toplayamaz; container log’a pivot etmek gerekir.
- **Admin workaround:**
  - Birincil: **System Events** tab’ı.
  - cron/deployments/db/cache için: container log / infra monitoring.
- **Escalation paketi:**
  - `GET /api/v1/logs/<category>` (cron/health/deployments/config/errors/queues/db/cache/archive)
  - Beklenen vs gerçek: anlamlı event listesi vs `[]`
  - Anahtar kelimeler: `logs/<category>`
- **Resolution owner:** Backend
- **Doğrulama (fix sonrası):** Event varsa her kategori endpoint’i non-empty döner; UI tab’lar dolar.

---

### 1.5 System → Admin Users → Users dışındaki tab’lar görünüyor ama endpoint’ler eksik olabilir

- **ID:** G-005
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** High

- **Kaynak sayfa:** `/docs/new/tr/admin/system/admin-users.md`
- **Belirti:** UI’da Roles/Teams/Sessions/Invites/Security sekmeleri var, ama istekler **404 Not Found** dönüyor.
- **Muhtemel neden:** UI `/api/v1/admin/roles`, `/api/v1/admin/sessions`, `/api/v1/admin/invites` gibi endpoint’leri çağırıyor; backend bu route’ları sağlamıyor.
- **Etki:** Sadece Users tab’ı çalışır; ileri admin/security operasyonları bloklanır.
- **Admin workaround:** Yok.
- **Escalation paketi:**
  - DevTools Network’ten fail eden path’leri yakalayın
  - Beklenen vs gerçek: 200 vs 404
  - Anahtar kelimeler: `admin/roles`, `admin/sessions`, `admin/invites`
- **Resolution owner:** Backend
- **Doğrulama (fix sonrası):** Endpoint’ler 200 döner ve UI tab’lar veri gösterir.

---

### 1.6 System → Feature Flags → Safe stub (persistence yok)

- **ID:** G-006
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** Medium

- **Kaynak sayfa:** `/docs/new/tr/admin/system/feature-flags.md`
- **Belirti:** Flag listesi boş; toggle OK döner ama state persist etmez.
- **Muhtemel neden:** `/api/v1/flags/*` route’ları bu build’de safe stub (return `[]` / return OK).
- **Etki:** Feature Flags prod rollout mekanizması olarak kullanılamaz.
- **Admin workaround:**
  - Incident gating için **Operations → Kill Switch** kullanın.
  - Persistence gelene kadar Feature Flags’ı “bilgilendirme” olarak düşünün.
- **Escalation paketi:**
  - `GET /api/v1/flags/`, `POST /api/v1/flags/`, `POST /api/v1/flags/{id}/toggle`
  - Beklenen vs gerçek: persisted state vs no persistence / empty
  - Anahtar kelimeler: `flags`, `toggle`
- **Resolution owner:** Backend
- **Doğrulama (fix sonrası):** Toggle refresh sonrası da persist eder; liste yeni state’i gösterir.

---

## 2) Notlar / süreç

- Yeni bir gap tespit edince şunları ekleyin:
  - modül / menü
  - tam endpoint
  - evidence link/ref (opsiyonel)
  - etki seviyesi (P0/P1/P2)
  - customer impact (opsiyonel)
- Register kısa ve aksiyon odaklı olmalı; derin analiz engineering ticket’larında yapılmalı.
