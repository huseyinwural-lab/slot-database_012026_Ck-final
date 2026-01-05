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
| G-001 | Games | Import 404 dönüyor | P1 | Backend | 7d | TBD | Open | Manuel config / import kullanma | Endpoint 200 döner; UI import başarılı |
| G-002 | System → API Keys | Toggle/patch 404 dönüyor | P1 | Backend | 7d | TBD | Open | Güvenli workaround yok (key’leri sabit tut) | Patch 200; UI toggle persist |
| G-003 | Reports / Simulator | Reports endpoint’leri ve simulator koşuları stub/404 | P1 | Backend | 7d | TBD | Open | Export-only / manuel analiz | Report endpoint’leri data döner; simulator run endpoint’leri var |

> SLA default: P0=24h, P1=7d, P2=30d.

---


> Bu register, menü sayfalarındaki “Backend/Integration Gap’leri” bölümlerini tamamlar.
> Bir gap doğrulandığında, aksiyon takibi için buraya ekleyin.

## 1) Açık gap’ler (modül bazlı)

### 1.1 System → Logs → Kategori endpoint’leri boş liste dönüyor

- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
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

### 1.2 System → Admin Users → Users dışındaki tab’lar görünüyor ama endpoint’ler eksik olabilir

- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
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

### 1.3 System → Feature Flags → Safe stub (persistence yok)

- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
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
