# Yönetim Paneli Kullanım Kılavuzu (TR) — Menü Bazlı

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Platform Engineering  

Bu doküman, Admin Panel için **menü bazlı ve ops-dayanıklı** bir kullanım kılavuzudur.
Amaç:
- her menünün ne işe yaradığını açıklamak
- sık yapılan işlemleri (oyun yükleme/içe aktarma, rapor export, simülasyon) adım adım tarif etmek
- olası arızalarda deterministik kontrol listesi ile çözüm sunmak

> EN ana kaynaktır. TR dokümanı, menüyü UI’da bulabilmeniz için Türkçe başlık + parantez içinde UI label içerir.

---

## Global arıza giderme kuralları (her yerde geçerli)

Bir şey fail olduğunda önce **3 bilgiyi** mutlaka al:
1) Fail olan request URL (DevTools → Network)
2) Status code (0/401/403/404/409/429/500)
3) Response body / error mesajı (1–2 satır)

Sonra:
- **write aksiyonu** ise (toggle/onay/import/create/update): **System → Audit Log**’a bak.
- **runtime error** ise (timeout/500): **System → Logs → Error Logs**’a bak.

En iyi arama anahtarları:
- `request_id` (varsa)
- domain ID’ler: `player_id`, `tx_id`, `job_id`, `tenant_id`, `campaign_id`

---

## Yetki / görünürlük (menüler neden görünür veya görünmez)

Menüler şu nedenle görünmeyebilir:
- owner-only / tenant-only
- capability flag’leri (feature gate)

Referans:
- `frontend/src/config/menu.js`
- `frontend/src/components/Layout.jsx`

---

# Core

## Gösterge Paneli (Dashboard)

**Ne işe yarar?**
Kritik metriklerin ve son aktivitelerin operasyonel özetini verir.

**İlgili API endpoint’leri (UI’ın kullandıkları)**
- `GET /api/v1/dashboard/comprehensive-stats`

**Log / Audit nerede aranır?**
- Widget boşsa: System → Logs → Error Logs
- 401 ise: tekrar login; Admin Users → Sessions kontrol

---

## Oyuncular (Players)

**Ne işe yarar?**
Oyuncu hesaplarını arama, inceleme ve yönetme.

**Alt başlıklar (ekran/sekme)**
- Oyuncu Listesi (`/players`)
- Oyuncu Detayı (`/players/:id`) sekmeleri:
  - Profil (Profile)
  - KYC
  - Finans (Finance)
  - Oyunlar (Games)
  - Loglar (Logs)
  - Notlar (Notes)

**İlgili API endpoint’leri (UI’ın kullandıkları)**
- Liste/arama:
  - `GET /api/v1/players`
- Oyuncu detayı:
  - `GET /api/v1/players/{player_id}`
  - `PUT /api/v1/players/{player_id}`
- Oyuncu finans:
  - `GET /api/v1/players/{player_id}/transactions`
  - `POST /api/v1/players/{player_id}/balance`
- Oyuncu KYC:
  - `GET /api/v1/players/{player_id}/kyc`
  - `POST /api/v1/kyc/{doc_id}/review`
- Oyuncu logları:
  - `GET /api/v1/players/{player_id}/logs`

**Log / Audit nerede aranır?**
- Sayfa load fail: System → Logs → Error Logs
- Oyuncu edit/balance: System → Audit Log (`resource_type=player` veya zaman aralığı)

**Olası hatalar & çözümler**
| Belirti | Olası neden | Çözüm |
|---|---|---|
| Oyuncu sayfası açılmıyor | API hata / auth | Fail request + login durumunu kontrol et |
| KYC sekmesi boş | KYC kapalı veya doküman yok | capability + oyuncu state kontrol |
| Balance fail | permission/policy | Audit Log + response body kontrol |

---

## Finans (Finance) (sadece owner)

**Ne işe yarar?**
İşlemler, uzlaştırma, chargeback ve raporlar.

**Alt başlıklar (sekme)**
- İşlemler (Transactions)
- Raporlar (Reports)
- Uzlaştırma (Reconciliation)
- Chargebacks

**İlgili API endpoint’leri (UI’ın kullandıkları)**
- `GET /api/v1/finance/transactions`
- `GET /api/v1/finance/reports`

**Log / Audit nerede aranır?**
- 500/timeout: System → Logs → Error Logs
- manuel state değişimi: System → Audit Log

---

## Para Çekimler (Withdrawals) (sadece owner)

**Ne işe yarar?**
Para çekme taleplerini inceleme ve işleme.

**İş akışı aksiyonları**
- Liste
- Recheck
- Review (approve/reject)
- Payout
- Mark Paid

**İlgili API endpoint’leri (UI’ın kullandıkları)**
- `GET /api/v1/finance/withdrawals`
- `POST /api/v1/finance/withdrawals/{tx_id}/recheck`
- `POST /api/v1/finance/withdrawals/{tx_id}/review`
- `POST /api/v1/finance/withdrawals/{tx_id}/payout`
- `POST /api/v1/finance/withdrawals/{tx_id}/mark-paid`

**Log / Audit nerede aranır?**
- payout/review/mark-paid: System → Audit Log (tx_id/time window)
- provider/webhook: System → Logs → Error Logs + webhook runbook

---

## Tüm Gelirler (All Revenue) (sadece owner)

**Ne işe yarar?**
Tenant’lar arası gelir analizi.

**İlgili API endpoint’leri**
- `GET /api/v1/reports/revenue/all-tenants`

---

## Benim Gelirim (My Revenue) (tenant-only)

**Ne işe yarar?**
Aktif tenant için gelir analizi.

**İlgili API endpoint’leri**
- `GET /api/v1/reports/revenue/my-tenant`

---

## Oyunlar (Games)

**Ne işe yarar?**
Oyun kataloğunu yönetme ve yeni oyun bundle’larını import ile ekleme.

**Alt başlıklar (sekme)**
- Slotlar ve Oyunlar (Slots & Games)
- Canlı Masalar (Live Tables)
- Yükleme ve İçe Aktarma (Upload & Import)

### Slotlar ve Oyunlar (Slots & Games)

**İlgili API endpoint’leri**
- `GET /api/v1/games`
- `POST /api/v1/games/{game_id}/toggle`

**Log / Audit**
- Toggle: System → Audit Log (`resource_type=game`)

### Canlı Masalar (Live Tables)

**İlgili API endpoint’leri**
- `GET /api/v1/tables`
- `POST /api/v1/tables`

### Yükleme ve İçe Aktarma (Upload & Import)

**Adım adım: oyun yükleme/içe aktarma**
1) Oyunlar → Yükleme ve İçe Aktarma
2) Tip seç (HTML5 / Unity)
3) Dosya seç
4) Upload & Analyze
5) Preview incele
6) Import This Game

**İlgili API endpoint’leri**
- `POST /api/v1/game-import/manual/upload`
- `GET /api/v1/game-import/jobs/{job_id}`
- `POST /api/v1/game-import/jobs/{job_id}/import`

**Log / Audit**
- job fail: System → Logs → Error Logs (job_id ile ara)
- catalog mutation: Audit Log

---

## VIP Oyunlar (VIP Games)

**Ne işe yarar?**
VIP oyun işaretleme/ayarlar.

**İlgili API endpoint’leri**
- `GET /api/v1/games`
- `PUT /api/v1/games/{game_id}/details`

---

# Operations

## KYC Doğrulama (KYC Verification)

**İlgili API endpoint’leri**
- `GET /api/v1/kyc/dashboard`
- `GET /api/v1/kyc/queue`
- `POST /api/v1/kyc/documents/{doc_id}/review`

**Log / Audit**
- review: Audit Log (resource_type=kyc)

---

## CRM ve İletişim (CRM & Comms)

**İlgili API endpoint’leri**
- `GET /api/v1/crm/campaigns`
- `GET /api/v1/crm/templates`
- `GET /api/v1/crm/segments`
- `GET /api/v1/crm/channels`
- `POST /api/v1/crm/campaigns`
- `POST /api/v1/crm/campaigns/{campaign_id}/send`

---

## Bonuslar (Bonuses)

**İlgili API endpoint’leri**
- `GET /api/v1/bonuses/campaigns`
- `POST /api/v1/bonuses/campaigns`
- `POST /api/v1/bonuses/campaigns/{id}/status`

---

## Affiliate’ler (Affiliates)

**İlgili API endpoint’leri**
- `GET /api/v1/affiliates`
- `GET /api/v1/affiliates/offers`
- `GET /api/v1/affiliates/links`
- `GET /api/v1/affiliates/payouts`
- `GET /api/v1/affiliates/creatives`
- `POST /api/v1/affiliates`
- `POST /api/v1/affiliates/offers`
- `POST /api/v1/affiliates/links`
- `POST /api/v1/affiliates/payouts`
- `POST /api/v1/affiliates/creatives`
- `PUT /api/v1/affiliates/{id}/status`

---

## Acil Durdurma (Kill Switch) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/tenants/`
- `POST /api/v1/kill-switch/tenant`

**Log / Audit**
- Kill switch değişiklikleri: Audit Log

---

## Destek (Support)

**İlgili API endpoint’leri**
- `GET /api/v1/support/dashboard`
- `GET /api/v1/support/tickets`
- `GET /api/v1/support/chats`
- `GET /api/v1/support/kb`
- `GET /api/v1/support/canned`
- `POST /api/v1/support/tickets/{ticket_id}/message`
- `POST /api/v1/support/canned`

---

# Risk & Compliance

## Risk Kuralları (Risk Rules) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/risk/dashboard`
- `GET /api/v1/risk/rules`
- `POST /api/v1/risk/rules`
- `POST /api/v1/risk/rules/{id}/toggle`
- `GET /api/v1/risk/velocity`
- `GET /api/v1/risk/blacklist`
- `POST /api/v1/risk/blacklist`
- `GET /api/v1/risk/cases`
- `PUT /api/v1/risk/cases/{case_id}/status`
- `GET /api/v1/risk/alerts`
- `GET /api/v1/risk/evidence`
- `POST /api/v1/risk/evidence`

---

## Fraud Kontrolü (Fraud Check) (sadece owner)

**İlgili API endpoint’leri**
- `POST /api/v1/fraud/analyze`

---

## Onay Kuyruğu (Approval Queue) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/approvals/requests?status=...`
- `GET /api/v1/approvals/rules`
- `GET /api/v1/approvals/delegations`
- `POST /api/v1/approvals/requests/{request_id}/action`

---

## Sorumlu Oyun (Responsible Gaming) (sadece owner)

**İlgili API endpoint’leri**
- `POST /api/v1/rg/admin/override/{player_id}`

---

# Game Engine

## Robotlar (Robots)

**İlgili API endpoint’leri**
- `GET /api/v1/robots`
- `POST /api/v1/robots/{robot_id}/toggle`
- `POST /api/v1/robots/{robot_id}/clone`

---

## Matematik Varlıkları (Math Assets)

**İlgili API endpoint’leri**
- `GET /api/v1/math-assets`
- `POST /api/v1/math-assets`

---

# System

## CMS (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/cms/dashboard`
- `GET /api/v1/cms/pages`
- `POST /api/v1/cms/pages`
- `GET /api/v1/cms/banners`
- `GET /api/v1/cms/collections`
- `GET /api/v1/cms/popups`
- `GET /api/v1/cms/translations`
- `GET /api/v1/cms/media`
- `GET /api/v1/cms/legal`
- `GET /api/v1/cms/experiments`
- `GET /api/v1/cms/audit`

---

## Raporlar (Reports)

**İlgili API endpoint’leri**
- `GET /api/v1/reports/overview`
- `GET /api/v1/reports/financial`
- `GET /api/v1/reports/players/ltv`
- `GET /api/v1/reports/games`
- `GET /api/v1/reports/providers`
- `GET /api/v1/reports/bonuses`
- `GET /api/v1/reports/affiliates`
- `GET /api/v1/reports/risk`
- `GET /api/v1/reports/rg`
- `GET /api/v1/reports/kyc`
- `GET /api/v1/reports/crm`
- `GET /api/v1/reports/cms`
- `GET /api/v1/reports/operational`
- `GET /api/v1/reports/schedules`
- `GET /api/v1/reports/exports`
- `POST /api/v1/reports/exports`

**Log / Audit**
- Export fail: Logs → Error Logs

---

## Loglar (Logs) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/logs/events`
- `GET /api/v1/logs/cron`
- `POST /api/v1/logs/cron/run`
- `GET /api/v1/logs/health`
- `GET /api/v1/logs/deployments`
- `GET /api/v1/logs/config`
- `GET /api/v1/logs/errors`
- `GET /api/v1/logs/queues`
- `GET /api/v1/logs/db`
- `GET /api/v1/logs/cache`
- `GET /api/v1/logs/archive`

---

## Denetim Kaydı (Audit Log) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/audit/events`
- `GET /api/v1/audit/export`

---

## Admin Kullanıcıları (Admin Users)

**İlgili API endpoint’leri**
- `GET /api/v1/tenants/`
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users`
- `GET /api/v1/admin/roles`
- `GET /api/v1/admin/teams`
- `GET /api/v1/admin/sessions`
- `GET /api/v1/admin/invites`
- `GET /api/v1/admin/keys`
- `GET /api/v1/admin/security`
- `GET /api/v1/admin/activity-log?...`
- `GET /api/v1/admin/login-history?...`
- `GET /api/v1/admin/permission-matrix`
- `GET /api/v1/admin/ip-restrictions`
- `POST /api/v1/admin/ip-restrictions`
- `GET /api/v1/admin/device-restrictions`
- `PUT /api/v1/admin/device-restrictions/{device_id}/approve`

---

## Tenant’lar (Tenants) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/tenants/`
- `POST /api/v1/tenants/`
- `PATCH /api/v1/tenants/{tenant_id}`

---

## API Anahtarları (API Keys) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/api-keys/`
- `GET /api/v1/api-keys/scopes`
- `POST /api/v1/api-keys/`
- `PATCH /api/v1/api-keys/{id}`

---

## Özellik Bayrakları (Feature Flags) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/flags/`
- `GET /api/v1/flags/experiments`
- `GET /api/v1/flags/segments`
- `GET /api/v1/flags/audit-log`
- `GET /api/v1/flags/environment-comparison`
- `GET /api/v1/flags/groups`
- `POST /api/v1/flags/{flag_id}/toggle`
- `POST /api/v1/flags/kill-switch`
- `POST /api/v1/flags/`
- `POST /api/v1/flags/experiments/{exp_id}/start`
- `POST /api/v1/flags/experiments/{exp_id}/pause`

---

## Simülatör (Simulator)

**İlgili API endpoint’leri**
- `GET /api/v1/simulation-lab/runs`

---

## Ayarlar (Settings) (sadece owner)

**İlgili API endpoint’leri**
- `GET /api/v1/settings/brands`
- `GET /api/v1/settings/currencies`
- `GET /api/v1/settings/country-rules`
- `GET /api/v1/settings/platform-defaults`
- `GET /api/v1/settings/api-keys`
- `GET /api/version`
