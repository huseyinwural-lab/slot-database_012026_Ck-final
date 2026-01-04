# Admin Users (TR)

**Menü yolu (UI):** System → Admin Users  
**Frontend route:** `/admin` (tab: users)  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Tenant context doğrula: yanlış tenant’ta admin yaratmak güvenlik incident’idir.
- Password mode seç: **manual** vs **invite**.
- Lockout’larda Password Reset runbook; “hiç admin yok” senaryosunda Break-glass.
- UI’da kullanıcı oluştu mu doğrula ve Audit Log kanıtını kontrol et.

---

## 1) Amaç ve kapsam

Admin Users, mevcut tenant için admin hesaplarının yönetimidir (create + lifecycle). Yüksek risklidir: platforma kim erişebilir sorusunu yönetir.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin) (prod’da tek aktör önerilir).

---

## 3) Alt başlıklar / sekmeler

Mevcut UI (`frontend/src/pages/AdminManagement.jsx`):
- Users (Admin Users)
- Roles / Teams / Sessions / Invites / Security
- Activity Log / Permission Matrix / IP & Devices / Login History

Bu doküman öncelikle **Admin Users** lifecycle’a odaklanır.

---

## 4) Temel akışlar (adım adım)

### 4.1 Admin user listesini görüntüleme
1) System → Admin Users aç.
2) Aktif tab **Users** olmalı.

**API çağrıları (frontend’den gözlemlendi):**
- Liste: `GET /api/v1/admin/users`

### 4.2 Admin user oluşturma (manual password)
1) **Create Admin User** tıkla.
2) full_name, email, role, tenant_role, tenant_id (owner ise), password_mode=manual, password doldur.
3) Submit.

**API çağrıları:**
- Create: `POST /api/v1/admin/users`

### 4.3 Admin user oluşturma (invite mode)
1) password_mode=invite seç.
2) Submit.
3) Invite link’i kopyala.

**Backend davranışı:**
- status `invited` olur ve `invite_token` üretilir.

### 4.4 Admin enable/disable
Backend destekler:
- `POST /api/v1/admin/users/{admin_id}/status` body `{ is_active: true|false }`

**Önemli UI notu:** Bu build’de AdminManagement.jsx doğrudan status endpoint’ini çağırmıyor. UI’da kontrol yoksa gap kabul edilir.

---

## 5) Saha rehberi (pratik ipuçları)

- Least privilege rol kullan.
- Credential paylaşma.
- Invite link’lerini kısa süreli ve güvenli kanaldan ilet.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** Users listesi görünmüyor.
   - **Muhtemel neden:** owner değil; backend error.
   - **Çözüm:** platform owner ile dene; Network kontrol.
   - **Doğrulama:** `GET /api/v1/admin/users` 200.

2) **Semptom:** Create USER_EXISTS ile fail.
   - **Muhtemel neden:** email zaten var.
   - **Çözüm:** farklı email; gerekiyorsa eski user disable.
   - **Doğrulama:** create success.

3) **Semptom:** Invite oluştu ama token/link yok.
   - **Muhtemel neden:** UI res.data.invite_token göstermiyor.
   - **Çözüm:** response payload kontrol; token yoksa escalate.
   - **Doğrulama:** invite modal token gösterir.

4) **Semptom:** Yeni admin login olamıyor.
   - **Muhtemel neden:** status invited/disabled; şifre yanlış.
   - **Çözüm:** status active mi kontrol; şifreyi doğrula; gerekirse reset.
   - **Doğrulama:** login başarılı.

5) **Semptom:** Yanlış tenant admin’i oluşturuldu.
   - **Muhtemel neden:** tenant_id yanlış seçildi.
   - **Çözüm:** admin’i hemen disable; doğru tenant’ta yeniden oluştur.
   - **Doğrulama:** audit’te disable + correct create.

6) **Semptom:** 403 TENANT_OVERRIDE_FORBIDDEN.
   - **Muhtemel neden:** owner olmayan kullanıcı başka tenant’a admin yaratmaya çalıştı.
   - **Çözüm:** platform owner ile yap; bypass etme.
   - **Doğrulama:** owner ile create başarılı.

7) **Semptom:** UI’da enable/disable aksiyonu yok.
   - **Muhtemel neden:** UI `/status` kontrolünü sunmuyor.
   - **Çözüm:** frontend/backend’e escalate; lockout’ta break-glass sadece son çare.
   - **Doğrulama:** fix sonrası UI status toggle.

8) **Semptom:** User create için audit kanıtı yok.
   - **Muhtemel neden:** audit devre dışı veya fail.
   - **Çözüm:** Audit Log kontrol; audit service doğrula.
   - **Doğrulama:** `admin.user_created` event var.

9) **Semptom:** Şifre sıfırlama gerekiyor.
   - **Muhtemel neden:** kullanıcı şifreyi unuttu.
   - **Çözüm:** password-reset runbook.
   - **Doğrulama:** reset sonrası login başarılı.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Roles/Teams/Sessions/Invites tab’lerinde 404.
   - **Likely Cause:** UI `/api/v1/admin/roles`, `/teams`, `/sessions`, `/invites` gibi endpoint’leri çağırıyor; backend implement etmeyebilir.
   - **Impact:** Sadece Users çalışır; gelişmiş admin/security özellikleri bloklanır.
   - **Admin Workaround:** No admin-side workaround.
   - **Escalation Package:**
     - Method + path: DevTools’tan fail eden path
     - Expected vs actual: expected 200; actual 404
     - Log keyword: `admin/roles` / `admin/sessions` / `admin/invites`
   - **Resolution Owner:** Backend
   - **Verification:** endpoint’ler 200 döner ve tab’ler dolu.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Yeni admin listede görünür.

### 8.2 System → Audit Log
- Şunları ara:
  - `admin.user_created`
  - `admin.user_updated`
  - `admin.user_enabled` / `admin.user_disabled`

### 8.3 System → Logs / container log
- Şunları ara:
  - `admin.user_created`
  - email hash event’leri
  - `TENANT_OVERRIDE_FORBIDDEN`

### 8.4 DB audit (varsa)
- `adminuser` kaydı doğru tenant_id ve status ile var.

---

## 9) Güvenlik notları + geri dönüş

- Admin user create security-critical.
- Geri dönüş:
  - yanlış oluşturulan admin’i disable et
  - leak şüphesi varsa credential rotation

---

## 10) İlgili linkler

- Password reset: `/docs/new/tr/runbooks/password-reset.md`
- Break-glass: `/docs/new/tr/runbooks/break-glass.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
