# Backend Gap Register (TR)

**Son gden geirme:** 2026-01-04  
**Sorumlu:** Platform Engineering / Ops  

Bu register, Admin Panel dokmanasyon srecinde tespit edilen **UI  Backend uyumsuzluklar**n tek yerde toplar.

**Nas kullan
- Her kay tket

> EN dokman tek do

---

## 1) A (mod bazl)

### 1.1 System → Logs → Kategori endpointleri bo liste dndyor

- **Kaynak sayfa:** `/docs/new/tr/admin/system/logs.md`
- **Belirti:**  tablar `[]` dndyor /  "No logs found" gsteriyor.
- **Muhtemel neden:** `backend/app/routes/logs.py` iinde `/events` var, ama birok kategori endpoint stub / bo dner.
- **Etki:** Ops Logs UIna kan olamaz; container loglarna pivot gerekir.
- **Admin workaround:**
  - Birincil: **System Events** tab.
  - cron/deployments/db/cache i infra monitoring + container log.
- **Escalation paketi:**
  - `GET /api/v1/logs/<category>` (cron/health/deployments/config/errors/queues/db/cache/archive)
  - Beklenen vs gerek: event listesi vs `[]`
  - Anahtar kelimeler: `logs/<category>`
- **Resolution owner:** Backend
- **Do (fix sonras):** Event varsa her kategori endpoint non-empty dner; UI tablar dol.

---

### 1.2 System → Admin Users → Users d tablar gsteriliyor ama endpointler eksik olabilir

- **Kaynak sayfa:** `/docs/new/tr/admin/system/admin-users.md`
- **Belirti:** UIda Roles/Teams/Sessions/Invites/Security sekmeleri var, ama istekler **404 Not Found** dndyor.
- **Muhtemel neden:** UI `/api/v1/admin/roles`, `/api/v1/admin/sessions`, `/api/v1/admin/invites` gibi endpointleri 
- **Etki:** Sadece Users tab ; ileri admin/security ilevleri blok.
- **Admin workaround:** Yok.
- **Escalation paketi:**
  - DevTools Network
  - Beklenen vs gerek: 200 vs 404
  - Anahtar kelime: `admin/roles`, `admin/sessions`, `admin/invites`
- **Resolution owner:** Backend
- **Do (fix sonras):** Endpointler 200 dner ve UI tablar dol.

---

### 1.3 System → Feature Flags → Safe stub (kal

- **Kaynak sayfa:** `/docs/new/tr/admin/system/feature-flags.md`
- **Belirti:** Flag listesi bo; toggle OK dner ama state persist etmez.
- **Muhtemel neden:** `/api/v1/flags/*` routeleri bu buildda safe stub (return `[]` / return OK).
- **Etki:** Feature Flags prod rollout i i.
- **Admin workaround:**
  - Incident gating i: **Operations → Kill Switch** kullan.
  - Persistence gelene kadar Feature Flags: .
- **Escalation paketi:**
  - `GET /api/v1/flags/`, `POST /api/v1/flags/`, `POST /api/v1/flags/{id}/toggle`
  - Beklenen vs gerek: persisted state vs no persistence / empty
  - Anahtar kelimeler: `flags`, `toggle`
- **Resolution owner:** Backend
- **Do (fix sonras):** Toggle refresh sonras bile persist eder; liste yeni state.

---

## 2) Notlar / s

- Yeni bir gap tespit edince  ekleyin:
  - mod / men
  - tam endpoint
  - screenshot veya request/response snippet (ticket)
  - etki seviyesi (P0/P1/P2)
- Register: ksa ve aksiyon odakl olsun; derin analiz engineering ticketlarlarda olmal.
