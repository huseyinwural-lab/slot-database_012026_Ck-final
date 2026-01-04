# Robots (TR)

**Menü yolu (UI):** Game Engine → Robots  
**Frontend route:** `/robots`  
**Feature flag (UI):** `can_use_game_robot`  

---

## Ops Checklist (read first)

- Robots, oyunların **math engine** tanımlarını yönetmek için kullanılır.
- Riskli işlemler:
  - robot toggle (oyun davranışını etkileyebilir)
  - robot clone (yeni config versiyonu üretir)
- Write işlemlerinde **reason** zorunlu (backend enforce eder).
- Değişiklikleri şuralarda doğrula:
  - UI (status değişimi)
  - **Audit Log** (`ROBOT_TOGGLE`, `ROBOT_CLONE`)
  - **Logs** (robots endpoint 4xx/5xx)

---

## 1) Amaç ve kapsam

Robots, **Game Math Engine** registry’sidir.
RobotDefinition genellikle Math Asset referanslarını `config` içinde taşır:
- `reel_set_ref`
- `paytable_ref`

Frontend: `frontend/src/pages/RobotsPage.jsx`.
Backend: `backend/app/routes/robots.py`.

---

## 2) Kim kullanır / yetki gereksinimi

- Game Ops / Game Engine ekibi
- Platform Owner (governance’e göre)

Erişim:
- UI: `can_use_game_robot`
- Backend: admin auth

---

## 3) UI’da neler var?

- Robot arama
- Robot config JSON görüntüleme
- Active/Inactive toggle
- Robot clone

> Not: UI’da “sıfırdan create” akışı yok; versiyonlama için clone yaklaşımı kullanılıyor.

---

## 4) Temel akışlar

### 4.1 Robot listeleme/arama
1) Game Engine → Robots aç.
2) Search input ile filtrele.

**API çağrıları (UI):**
- `GET /api/v1/robots?search=<text>`

Beklenen response:
- `{ items: RobotDefinition[], meta: { total, page, page_size } }`

### 4.2 Robot config görüntüleme
1) Eye ikonu.
2) JSON incele.

**Kaynak:** robot objesi `config`.

### 4.3 Robot aktif/pasif toggle
1) Switch’i değiştir.
2) Reason ver (backend ister).

**API çağrıları:**
- `POST /api/v1/robots/{robot_id}/toggle`

**Audit event (beklenen):**
- `ROBOT_TOGGLE`

### 4.4 Robot clone
1) Clone tıkla.
2) Reason ver.

**API çağrıları:**
- `POST /api/v1/robots/{robot_id}/clone`

**Audit event (beklenen):**
- `ROBOT_CLONE`

---

## 5) Saha rehberi (pratik ipuçları)

- Konfigürasyon değişikliklerini pratikte immutable kabul et; değişiklik için clone.
- İsim standardı:
  - `game_x_v1`, `game_x_v2`.
- Robot enable etmeden önce referans Math Asset’lerin mevcut olduğundan emin ol.

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Robots sayfası boş.
   - **Muhtemel neden:** robot yok veya tenant context mismatch.
   - **Çözüm:** seed; tenant context kontrol.
   - **Doğrulama:** GET items döner.

2) **Belirti:** Robots list 401.
   - **Muhtemel neden:** session expired.
   - **Çözüm:** tekrar login.
   - **Doğrulama:** GET 200.

3) **Belirti:** Robots list 403.
   - **Muhtemel neden:** `can_use_game_robot` yok.
   - **Çözüm:** feature ver.
   - **Doğrulama:** route erişilebilir.

4) **Belirti:** Toggle 400 REASON_REQUIRED.
   - **Muhtemel neden:** reason yok.
   - **Çözüm:** `X-Reason` header veya client’in istediği reason alanını gönder.
   - **Doğrulama:** toggle 200.

5) **Belirti:** Toggle 404.
   - **Muhtemel neden:** robot_id yok.
   - **Çözüm:** listeyi refresh et.
   - **Doğrulama:** robot bulunur.

6) **Belirti:** Clone 400 REASON_REQUIRED.
   - **Muhtemel neden:** reason yok.
   - **Çözüm:** reason ekle.
   - **Doğrulama:** clone 200.

7) **Belirti:** Clone 422.
   - **Muhtemel neden:** backend embed `name_suffix` bekliyor.
   - **Çözüm:** default bırak; override gerekiyorsa `{ "name_suffix": " (Cloned)" }` gönder.
   - **Doğrulama:** yeni robot listede.

8) **Belirti:** Audit Log’da robot değişiklikleri görünmüyor.
   - **Muhtemel neden:** audit persist edilmiyor veya filtre yanlış.
   - **Çözüm:** Audit Log route/filter kontrol.
   - **Doğrulama:** `ROBOT_TOGGLE`/`ROBOT_CLONE` görünür.

9) **Belirti:** Robot enable ama oyun davranışı değişmiyor.
   - **Muhtemel neden:** game binding ayrı (GameRobotBinding).
   - **Çözüm:** game binding workflow’larını doğrula.
   - **Doğrulama:** oyun doğru robot_id’yi referanslar.

---

## 7) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI reason istemiyor; backend reason zorunlu.
   - **Muhtemel neden:** `toggle_robot` ve `clone_robot` `require_reason` kullanıyor.
   - **Etki:** toggle/clone REASON_REQUIRED ile fail olabilir.
   - **Admin workaround:** yok.
   - **Escalation paketi:** toggle/clone 400 response.
   - **Resolution owner:** Frontend/Backend

2) **Belirti:** “Robot create” akışı yok.
   - **Muhtemel neden:** clone ile versiyonlama tercih edilmiş.
   - **Etki:** template robot olmadan yeni robot oluşturulamaz.
   - **Resolution owner:** Product

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Toggle badge değiştirir.
- Clone yeni satır ekler.

### 8.2 System → Logs
- `/api/v1/robots` 4xx/5xx kontrol.

### 8.3 System → Audit Log
- `ROBOT_TOGGLE`, `ROBOT_CLONE` filtre.

### 8.4 DB doğrulama
- `robotdefinition` satırları.

---

## 9) Güvenlik notları + rollback

- Robot enable game outcomes değiştirebilir.
- Rollback:
  - toggle geri al
  - veya binding’i eski robot versiyonuna çevir

---

## 10) İlgili linkler

- Math Assets: `/docs/new/tr/admin/game-engine/math-assets.md`
- Simulator: `/docs/new/tr/admin/system/simulator.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
