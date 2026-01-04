# Yönetim Paneli Kullanım Kılavuzu (TR) — Menü Bazlı

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Platform Engineering  

Bu doküman, Admin Panel için **menü bazlı ve ops-dayanıklı** bir kullanım kılavuzudur.
Amaç:
- her menünün ne işe yaradığını açıklamak
- sık yapılan işlemleri (oyun yükleme/import, rapor export, simülasyon) adım adım tarif etmek
- olası arızalarda deterministik kontrol listesi ile çözüm sunmak

> EN ana kaynaktır. TR mirror: `/docs/new/tr/guides/admin-panel-manual.md`.
> Menüleri UI’da hızlı bulabilmeniz için başlıklarda Türkçe + parantez içinde UI label kullanılır.

---

## Bu kılavuzun yapısı

Her menü için standart şablon:
1) Ne işe yarar?
2) Alt başlıklar (alt menü / sekme)
3) Sık yapılan işlemler (adım adım)
4) Olası hatalar & çözümler
5) Yetki/görünürlük notları

---

# Core

## Gösterge Paneli (Dashboard)

**Ne işe yarar?**
Kritik metriklerin ve son aktivitelerin operasyonel özetini verir.

**Sık yapılan işlemler**
- Aktif tenant bağlamının doğru olduğunu kontrol et (tenant switcher).

**Olası hatalar & çözümler**
- Widget’lar boş / veri yok → tenant bağlamını ve API erişimini kontrol et.

---

## Oyuncular (Players)

**Ne işe yarar?**
Oyuncu hesaplarını arama, inceleme ve yönetme.

**Ekranlar / Alt başlıklar**
- Oyuncu Listesi (`/players`)
- Oyuncu Detayı (`/players/:id`) sekmeleri:
  - Profil (Profile)
  - KYC
  - Finans (Finance)
  - Oyunlar (Games)
  - Loglar (Logs)
  - Notlar (Notes)

**Sık yapılan işlemler**
1) Oyuncu bulma
- Oyuncular listesinden filtre/arama kullan.
- Gerekirse üst bardaki Global Search (Ctrl+K) kullan.

2) Oyuncu KYC inceleme
- Oyuncu Detayı → KYC sekmesi.

3) Oyuncu bakiyesi ayarlama (aktifse)
- Oyuncu Detayı → Finans sekmesi (aksiyonlar yetkiye bağlıdır).

**Olası hatalar & çözümler**
| Belirti | Olası neden | Çözüm |
|---|---|---|
| Oyuncu sayfası açılmıyor | API hata / auth | `/api/v1/players/{id}` isteğini ve login durumunu kontrol et |
| KYC sekmesi boş | KYC kapalı veya doküman yok | feature flag/capability ve oyuncu KYC durumunu kontrol et |

---

## Finans (Finance) (sadece owner)

**Ne işe yarar?**
Finansal operasyonlar: işlemler, uzlaştırma, chargeback, raporlar.

**Alt başlıklar (sekme)**
- İşlemler (Transactions)
- Raporlar (Reports)
- Uzlaştırma (Reconciliation)
- Chargebacks

**Olası hatalar & çözümler**
- 403 forbidden → platform owner değilsin (owner-only).

---

## Para Çekimler (Withdrawals) (sadece owner)

**Ne işe yarar?**
Para çekme taleplerini inceleme ve işleme.

**Uygulama notu**
Bu akış UI’da `FinanceWithdrawals.jsx` üzerinden yönetilir ve aksiyonlar şunları içerebilir:
- payout
- recheck
- review (approve/reject)
- mark paid

**Sık yapılan işlemler (üst seviye)**
1) Para Çekimler ekranını aç
2) Bekleyenleri filtrele
3) Seçili işlem için:
- Recheck
- Review
- Payout
- Mark Paid

**Olası hatalar & çözümler**
| Belirti | Olası neden | Çözüm |
|---|---|---|
| Payout fail | provider/webhook state uyumsuz | backend log + payout status kontrol; webhooks doğrula |
| UI “Network Error” | proxy/baseURL | istek `/api/...` gidiyor mu kontrol et |

---

## Tüm Gelirler (All Revenue) (sadece owner)

**Ne işe yarar?**
Platform owner için tenant’lar arası toplam gelir analizi.

---

## Oyunlar (Games)

**Ne işe yarar?**
Oyun kataloğunu yönetme ve yeni oyun bundle’larını upload/import ile sisteme ekleme.

**Alt başlıklar (sekme)**
- Slotlar ve Oyunlar (Slots & Games)
- Canlı Masalar (Live Tables)
- Yükleme ve İçe Aktarma (Upload & Import)

### Slotlar ve Oyunlar (Slots & Games)

**Ne işe yarar?**
- katalog listesini görüntüleme
- oyun enable/disable (toggle)

**Sık yapılan işlem: oyun enable/disable**
1) Oyunlar → Slotlar ve Oyunlar
2) Oyunu bul
3) Toggle ile aktif/pasif yap (arka planda `/api/v1/games/{gameId}/toggle`)

**Olası hatalar & çözümler**
- Toggle fail → API response/permission/validation kontrol et.

### Canlı Masalar (Live Tables)

**Ne işe yarar?**
- provider tabanlı live table listelerini yönetme

**Olası hatalar & çözümler**
- Liste boş → provider entegrasyonu/tenant payment policy eksik olabilir.

### Yükleme ve İçe Aktarma (Upload & Import) (Game Import Wizard)

**Ne işe yarar?**
HTML5 veya Unity WebGL bundle upload edip analiz → preview → import akışı ile oyunu sisteme ekler.

**Adım adım: upload/import**
1) Oyunlar → Yükleme ve İçe Aktarma
2) Import tipi seç:
   - Upload HTML5 Game Bundle
   - Upload Unity WebGL Bundle
3) Client type seç (HTML5/Unity)
4) Dosya seç (bundle)
5) **Upload & Analyze** tıkla
6) "Manual Import Preview" sonuçlarını incele:
   - errors / warnings
7) Hata yoksa **Import This Game** tıkla

**Ops için arka plan notu**
- Analyze bir job oluşturur ve preview item’ları üretir.
- Import job’u finalize eder.

Kullanılan API’ler:
- `GET /api/v1/game-import/jobs/{job_id}`
- `POST /api/v1/game-import/jobs/{job_id}/import`

**Olası hatalar & çözümler**
| Belirti | Olası neden | Çözüm |
|---|---|---|
| Upload anında fail | dosya büyük / proxy limit | daha küçük bundle veya upload limitlerini infra tarafında artır |
| Preview validation error | manifest/assets hatalı | bundle yapısını düzeltip yeniden yükle |
| Import butonu kapalı | validation error var | önce hataları çöz; import bloklanır |

---

## VIP Oyunlar (VIP Games)

**Ne işe yarar?**
Oyunları VIP olarak işaretleme ve VIP görünürlük/ayarları.

---

# Operations

## KYC Doğrulama (KYC Verification)

**Ne işe yarar?**
Oyuncu KYC dokümanlarını inceleme ve doğrulama.

**Alt başlıklar (sekme)**
- Dashboard
- Verification Queue
- Rules & Levels

**Sık yapılan işlem: doküman onay/red**
1) KYC Doğrulama → Verification Queue
2) Dokümanı aç
3) Approve/Reject (arka planda `/api/v1/kyc/.../review`)

---

## CRM ve İletişim (CRM & Comms)

**Ne işe yarar?**
Kampanya oluşturma ve gönderim.

**Alt başlıklar**
- Campaigns
- Templates
- Segments
- Channels

---

## Bonuslar (Bonuses)

**Ne işe yarar?**
Bonus kampanyalarını yönetme.

---

## Affiliate’ler (Affiliates)

**Ne işe yarar?**
Affiliate partner, offer, payout ve rapor yönetimi.

**Alt başlıklar (sekme)**
- Partners
- Offers
- Tracking
- Payouts
- Creatives
- Reports

---

## Acil Durdurma (Kill Switch) (sadece owner)

**Ne işe yarar?**
Yüksek riskli operasyonlar için acil durdurma.

---

## Destek (Support)

**Ne işe yarar?**
Ticket ve müşteri destek araçları.

**Alt başlıklar (sekme)**
- Overview
- Inbox
- Live Chat
- Help Center
- Config

---

# Risk & Compliance

## Risk Kuralları (Risk Rules) (sadece owner)

**Ne işe yarar?**
Risk kuralları oluşturma ve toggle.

---

## Fraud Kontrolü (Fraud Check) (sadece owner)

**Ne işe yarar?**
Fraud analizi ve vaka inceleme.

---

## Onay Kuyruğu (Approval Queue) (sadece owner)

**Ne işe yarar?**
Onay akışlarını yönetme.

**Alt başlıklar (sekme)**
- Pending
- Approved
- Rejected
- Policies
- Delegations

---

## Sorumlu Oyun (Responsible Gaming) (sadece owner)

**Ne işe yarar?**
Sorumlu oyun kontrolleri ve admin override.

---

# Game Engine

## Robotlar (Robots)

**Ne işe yarar?**
Game robot’ları yönetme (toggle/clone).

---

## Matematik Varlıkları (Math Assets)

**Ne işe yarar?**
Game math/model asset yönetimi.

---

# System

## CMS (sadece owner)

**Ne işe yarar?**
Sayfa/banner/media/legal/i18n gibi içerik yönetimi.

**Alt başlıklar (sekme)**
- Overview
- Pages
- Homepage
- Banners
- Collections
- Popups
- Media
- i18n
- Legal
- A/B Test
- System
- Audit

---

## Raporlar (Reports)

**Ne işe yarar?**
Rapor üretimi ve export.

**Alt başlıklar**
- Export Center
- diğer rapor grupları: financial, players, games, providers, bonuses, affiliates, crm, cms, scheduled

**Sık yapılan işlem: rapor export**
1) System → Reports
2) **Export Center** aç
3) Export tipini seç
4) Export iste (arka planda `POST /api/v1/reports/exports`)

---

## Loglar (Logs) (sadece owner)

**Ne işe yarar?**
Sistem loglarını inceleme.

---

## Denetim Kaydı (Audit Log) (sadece owner)

**Ne işe yarar?**
Değişiklikleri audit üzerinden görüntüleme.

**Alt başlıklar (sekme)**
- Changes (Diff)
- Before/After
- Metadata & Context
- Raw JSON

---

## Admin Kullanıcıları (Admin Users)

**Ne işe yarar?**
Admin kullanıcı/rol/oturum/invite/security yönetimi.

**Alt başlıklar (sekme)**
- Admin Users
- Roles
- Teams
- Activity Log
- Permission Matrix
- IP & Devices
- Login History
- Security
- Sessions
- Invites
- API Keys
- Risk Score
- Delegation

**Sık yapılan işlem: admin invite**
1) Admin Users → Invites
2) Invite oluştur
3) Invite linkini kopyala

---

## Tenant’lar (Tenants) (sadece owner)

**Ne işe yarar?**
Tenant oluşturma/yönetme.

---

## API Anahtarları (API Keys) (sadece owner)

**Ne işe yarar?**
Platform API key yönetimi.

---

## Özellik Bayrakları (Feature Flags) (sadece owner)

**Ne işe yarar?**
Feature flag ve experiment yönetimi.

**Alt başlıklar (sekme)**
- Feature Flags
- Experiments
- Segments
- Analytics
- Results
- Audit Log
- Env Compare
- Groups

---

## Simülatör (Simulator)

**Ne işe yarar?**
Simulation Lab: math/portfolio/bonus/risk modüllerinde senaryo çalıştırma.

**Alt başlıklar (sekme)**
- Overview
- Game Math
- Portfolio
- Bonus
- Cohort/LTV
- Risk
- RG
- A/B Sandbox
- Scenario Builder
- Archive

**Sık yapılan işlem: simülasyon çalıştırma**
1) System → Simulator
2) Bir modül seç (örn Risk)
3) Parametreleri gir
4) Run (varsa)
5) Sonuçları Archive altında incele

---

## Ayarlar (Settings) (sadece owner)

**Ne işe yarar?**
Platform ayar ve politikaları.

**Alt başlıklar (sekme)**
- Brands
- Domains
- Currencies
- Payment Providers
- Payments Policy
- Countries
- Games
- Communication
- Regulatory
- Defaults
- API Keys
- Theme
- Maintenance
- Versions
- Audit

---

## Menülerin görünürlüğü (özet)

Menüler şu nedenlerle görünmeyebilir:
- owner-only / tenant-only
- feature capability flag’leri
- backend capabilities

Referans:
- `frontend/src/config/menu.js`
- `frontend/src/components/Layout.jsx`
