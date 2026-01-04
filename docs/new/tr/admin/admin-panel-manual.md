# Yönetim Paneli Kullanım Kılavuzu (TR) — Hub

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Platform Engineering  

Bu doküman, Admin Panel kullanım kılavuzunun **hub** sayfasıdır.

- **Kapsam:** Navigasyon + her menünün detay sayfasına yönlendirme.
- **Tek doğru kaynak:** EN. TR, birebir senkron türevdir.
- **Kural:** Detay prosedürler **menü sayfalarında** yer alır. Runbook’lar (break-glass, şifre sıfırlama) `/docs/new/tr/runbooks/` altındadır.

---

## 0) Bu kılavuz nasıl kullanılır?

1) Aşağıdaki menü ağacından ilgili menüyü bulun.
2) İlgili menü sayfasını açın.
3) Her incident/aksiyonda mutlaka şunları toplayın:
   - failing request URL + status code (DevTools → Network)
   - `x-request-id` response header (varsa)
4) Sonucu, sayfanın **Doğrulama (UI + Logs + Audit + DB)** bölümünden doğrulayın.

---

## 1) Kritik güvenlik notları (prod operasyon öncesi okuyun)

### 1.1 Tenant context ve impersonation
- Platform Owner (Super Admin) `X-Tenant-ID` header ile tenant impersonation yapabilir.
- Tenant admin’ler tenant context’i **override edemez**.
- Yıkıcı aksiyonlardan önce doğru tenant’ta olduğunuzu doğrulayın.

### 1.2 API key’ler
- API key’ler prod seviyesinde secret’tır.
- Secret sadece create anında gösterilmelidir.
- Leak şüphesinde: revoke + rotation + audit kanıtı.

### 1.3 Kill Switch ve blast radius
- Kill switch yüksek blast-radius bir kontroldür.
- Kim, neden, hangi tenant/modül, rollback planı zorunlu.

### 1.4 Break-glass
- Break-glass kontrollü istisna sürecidir.
- Onay + post-mortem gerektirir.
- Runbook:
  - `/docs/new/tr/runbooks/break-glass.md`

---

## 2) Menü ağacı → sayfalar

> Menü kaynağı: `frontend/src/config/menu.js`

### Core

**Durum:** TAMAMLANDI (Dashboard + Players + Finance + Withdrawals + All Revenue + Games + VIP Games)

- Dashboard → `./core/dashboard.md`
- My Revenue (sadece tenant) → (aktifse Reports / Revenue menülerine bakın)
- Players → `./core/players.md`
- Finance (sadece owner) → `./core/finance.md`
- Withdrawals (sadece owner) → `./core/withdrawals.md`
- All Revenue (sadece owner) → `./core/all-revenue.md`
- Games → `./core/games.md`
- VIP Games → `./core/vip-games.md`

### Operations
- KYC Verification → `./operations/kyc-verification.md`
- CRM & Comms → `./operations/crm-comms.md`
- Bonuses → `./operations/bonuses.md`
- Affiliates → `./operations/affiliates.md`
- Kill Switch (sadece owner) → `./operations/kill-switch.md`
- Support → `./operations/support.md`

### Risk & Compliance
- Risk Rules (sadece owner) → `./risk-compliance/risk-rules.md`
- Fraud Check (sadece owner) → `./risk-compliance/fraud-check.md`
- Approval Queue (sadece owner) → `./risk-compliance/approval-queue.md`
- Responsible Gaming (sadece owner) → `./risk-compliance/responsible-gaming.md`

### Game Engine
- Robots → `./game-engine/robots.md`
- Math Assets → `./game-engine/math-assets.md`

### System
- CMS (sadece owner) → `./system/cms.md`
- Reports → `./system/reports.md`
- Logs (sadece owner) → `./system/logs.md`
- Audit Log (sadece owner) → `./system/audit-log.md`
- Admin Users → `./system/admin-users.md`
- Tenants (sadece owner) → `./system/tenants.md`
- API Keys (sadece owner) → `./system/api-keys.md`
- Feature Flags (sadece owner) → `./system/feature-flags.md`
- Simulator → `./system/simulator.md`
- Settings (sadece owner) → `./system/settings.md`

---

## 3) Global doğrulama lokasyonları (tüm menüler için)

### 3.1 UI doğrulama
- System → Audit Log (mutation: create/update/approve/toggle/import)
- System → Logs (runtime error/timeout)

### 3.2 Application / container log
- Backend (container log): `request_id`, `tenant_id` veya domain ID’ler (`player_id`, `tx_id`, `job_id`) ile arayın.

### 3.3 Database audit tabloları (varsa)
- Kanonik audit tablo: `auditevent`
- Diğer audit tabloları deploy’a göre değişebilir.

---

## 4) İlgili runbook’lar

- Şifre sıfırlama: `/docs/new/tr/runbooks/password-reset.md`
- Break-glass: `/docs/new/tr/runbooks/break-glass.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
