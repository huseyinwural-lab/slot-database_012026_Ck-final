# 🎰 Casino Admin Panel - Kapsamlı Kullanım Kılavuzu

## 📋 İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Dashboard](#dashboard)
3. [Player Management (Oyuncu Yönetimi)](#player-management)
4. [Game Management (Oyun Yönetimi)](#game-management)
5. [Finance Management (Finans Yönetimi)](#finance-management)
6. [Bonus Management (Bonus Yönetimi)](#bonus-management)
7. [Admin Users (Admin Kullanıcı Yönetimi)](#admin-users)
8. [Feature Flags & A/B Testing](#feature-flags)
9. [Simulation Lab](#simulation-lab)
10. [Settings Panel (Ayarlar)](#settings-panel)
11. [Risk & Fraud Management](#risk-fraud)
12. [Reports (Raporlar)](#reports)

---

## Genel Bakış

Casino Admin Panel, casino operatörleri için tasarlanmış enterprise-level bir yönetim platformudur. Oyuncu yönetiminden oyun konfigürasyonuna, bonus sistemlerinden risk yönetimine kadar tüm casino operasyonlarını tek bir yerden yönetebilirsiniz.

### Ana Özellikler
- 🎮 **Kapsamlı Oyun Yönetimi** - RTP ayarları, VIP masaları, custom tables
- 👥 **Detaylı Oyuncu Profilleri** - KYC, balance, game history, logs
- 💰 **Finans Modülü** - Deposit/withdrawal yönetimi, raporlar
- 🎁 **Gelişmiş Bonus Sistemi** - Şablonlar, kurallar, kampanyalar
- 🛡️ **Risk & Fraud Yönetimi** - AI destekli fraud detection
- 🧪 **Simulation Lab** - Oyun matematiği ve revenue simülasyonları
- 🏢 **Multi-Tenant** - Çoklu marka yönetimi

### Sistem Gereksinimleri
- Modern web tarayıcı (Chrome, Firefox, Safari, Edge)
- Minimum 1920x1080 çözünürlük önerilir
- Internet bağlantısı

---

## Dashboard

### Genel Bakış
Dashboard, casino operasyonlarınızın anlık durumunu gösterir.

### Ana KPI'lar
1. **GGR (Gross Gaming Revenue)** - Brüt oyun geliri
2. **NGR (Net Gaming Revenue)** - Net oyun geliri
3. **Active Players** - Aktif oyuncu sayısı
4. **Deposit Count** - Toplam deposit sayısı
5. **Withdrawal Count** - Toplam withdrawal sayısı

### Grafikler
- **Revenue Trend** - Son 7 günlük gelir trendi
- **Player Activity** - Oyuncu aktivite grafiği
- **Top Games** - En çok oynanan oyunlar
- **Payment Status** - Ödeme durumları

### Kullanım
1. Sol menüden "Dashboard" seçin
2. Tarih aralığını değiştirmek için sağ üstteki date picker'ı kullanın
3. Her KPI kartına tıklayarak detaylı rapor alabilirsiniz
4. "Refresh" butonu ile verileri güncelleyin

---

## Player Management

### Oyuncu Listesi

#### Filtreleme
Oyuncuları filtrelemek için:
1. **Search Bar** - Email, username veya player ID ile arama
2. **Status Filter** - Active, Suspended, Blocked
3. **VIP Level** - VIP seviyesine göre filtreleme
4. **Registration Date** - Kayıt tarihine göre

#### Sıralama
- Player ID
- Username
- Registration Date
- Total Deposits
- Last Login

#### Toplu İşlemler
- **Bulk Suspend** - Seçili oyuncuları askıya al
- **Bulk Export** - Excel/CSV export
- **Send Bulk Message** - Toplu mesaj gönder

### Oyuncu Detay Sayfası

#### Sekmeler

**1. Profile (Profil)**
- Temel bilgiler (Ad, email, telefon)
- VIP seviyesi
- Kayıt tarihi
- Son giriş
- Durum (Active/Suspended/Blocked)

**İşlemler:**
- ✏️ Edit Profile - Profil düzenle
- 🚫 Suspend Player - Oyuncuyu askıya al
- ⛔ Block Player - Oyuncuyu engelle
- 📧 Send Email - Email gönder

**2. KYC (Kimlik Doğrulama)**
- KYC seviyesi (Tier 1, 2, 3)
- Yüklenen belgeler
- Doğrulama durumu
- Doğrulama notları

**İşlemler:**
- ✅ Approve Document - Belgeyi onayla
- ❌ Reject Document - Belgeyi reddet
- 📤 Request Additional Documents - Ek belge iste

**3. Balance (Bakiye)**
- Real Money Balance - Gerçek para bakiyesi
- Bonus Balance - Bonus bakiyesi
- Locked Balance - Kilitli bakiye
- Total Wagering - Toplam bahis
- Pending Withdrawals - Bekleyen çekimler

**İşlemler:**
- ➕ Manual Credit - Manuel bakiye yükle
- ➖ Manual Debit - Manuel bakiye düş
- 🔒 Lock Balance - Bakiyeyi kilitle
- 📊 View Transaction History

**4. Game History (Oyun Geçmişi)**
- Oynanan oyunlar listesi
- Bet miktarları
- Win/Loss durumu
- RTP gerçekleşmeleri
- Son 100 oturum

**Filtreleme:**
- Tarih aralığı
- Oyun tipi
- Provider
- Win/Loss

**5. Transaction Log**
- Tüm finansal işlemler
- Deposits
- Withdrawals
- Bonuses
- Manual adjustments

**6. Activity Log**
- Login/logout kayıtları
- IP adresleri
- Cihaz bilgileri
- Şüpheli aktiviteler

---

## Game Management

### Oyun Listesi

#### Genel Ayarlar
Her oyun için:
- **Status** - Active/Inactive
- **RTP** - Return to Player yüzdesi
- **Min/Max Bet** - Minimum ve maksimum bahis limitleri
- **Volatility** - Oyun volatilitesi
- **Hit Frequency** - Kazanma frekansı

#### RTP Yönetimi

**RTP Profilleri:**
1. Standard (96.5%)
2. High (97.5%)
3. VIP (98%)
4. Custom (özel)

**RTP Değiştirme:**
```
1. Oyunu seçin
2. "Edit Game" butonuna tıklayın
3. "RTP Configuration" sekmesine gidin
4. Yeni RTP değerini girin
5. "Save Draft" -> Approval Queue'ye gönderilir
6. Super Admin onayı sonrası aktif olur
```

⚠️ **Önemli:** RTP değişiklikleri dual-control sisteminden geçer.

### VIP & Custom Tables

#### VIP Masa Oluşturma
```
1. "Game Management" -> "VIP Games" sekmesi
2. "Create VIP Table" butonuna tıklayın
3. Form doldur:
   - Table Name
   - Base Game ID
   - Min Bet (örn: $100)
   - Max Bet (örn: $10,000)
   - VIP Level Requirement (örn: Level 3)
   - Max Players
   - Special Features (opsiyonel)
4. "Create" butonuna tıklayın
```

**VIP Masa Özellikleri:**
- Yüksek bet limitleri
- Özel RTP profilleri
- Private room seçeneği
- Dedicated dealer (canlı oyunlar için)
- Special bonuses

### Paytable Yönetimi

Slot oyunları için symbol weights ve paytable konfigürasyonu:

```
1. Oyunu seçin
2. "Paytable Config" butonuna tıklayın
3. Her symbol için:
   - Reel weights (her makara için ağırlık)
   - Payout values (ödeme değerleri)
   - Scatter/Wild konfigürasyonu
4. "Save & Validate" - Otomatik RTP hesaplaması
5. "Submit for Approval"
```

### Jackpot Konfigürasyonu

**Jackpot Tipleri:**
1. **Fixed Jackpot** - Sabit jackpot
2. **Progressive Jackpot** - Artan jackpot
3. **Multi-Level Jackpot** - Mini, Minor, Major, Grand

**Ayarlar:**
- Seed Amount - Başlangıç miktarı
- Contribution % - Her bet'ten jackpot'a katkı yüzdesi
- Win Probability - Kazanma olasılığı
- Max Cap - Maksimum limit

---

## Finance Management

### Deposit Yönetimi

#### Deposit İstekleri
Pending deposit isteklerini görüntüleyin:

**Kolonlar:**
- Player ID/Username
- Amount
- Payment Method
- Status (Pending, Approved, Rejected)
- Request Time
- Processing Time

**İşlemler:**
1. **Approve** - Depozitoyu onayla
   - Otomatik olarak oyuncu bakiyesine eklenir
   - Transaction log oluşturulur
   - Oyuncuya email gönderilir

2. **Reject** - Depozitoyu reddet
   - Rejection reason seçin
   - Oyuncuya bildirim gönderilir

3. **Flag as Suspicious** - Şüpheli olarak işaretle
   - Risk engine'e gönderilir
   - Manual review gerektirir

### Withdrawal Yönetimi

#### Withdrawal İstekleri

**Onay Süreci:**
```
1. Pending Withdrawals listesini kontrol edin
2. Player profile'ı inceleyin
3. KYC durumunu kontrol edin
4. Recent activity'yi gözden geçirin
5. Fraud check sonuçlarına bakın
6. Approve veya Reject
```

**Otomatik Kontroller:**
- ✅ KYC Level kontrolü
- ✅ Wagering requirement karşılandı mı?
- ✅ Duplicate withdrawal check
- ✅ Velocity check (hız kontrolü)
- ✅ Device fingerprint match
- ✅ IP location match

**Rejection Sebepler:**
- KYC not completed
- Wagering not met
- Suspicious activity
- Document verification required
- Duplicate account suspected

### Financial Reports

#### Rapor Tipleri

**1. Daily Revenue Report**
- GGR/NGR breakdown
- By game provider
- By game category
- By player segment

**2. Deposit/Withdrawal Report**
- Success rates
- Average amounts
- By payment method
- Processing times

**3. Bonus Cost Report**
- Total bonus issued
- Bonus used
- Wagering completed
- ROI analysis

**Export Seçenekleri:**
- 📄 PDF
- 📊 Excel
- 📋 CSV
- 📧 Email Schedule (günlük/haftalık)

---

## Bonus Management

### Bonus Şablonları

#### Bonus Tipleri

**1. Welcome Bonus**
```yaml
Örnek Konfigürasyon:
- Type: Deposit Match
- Percentage: 100%
- Max Amount: $500
- Wagering: 35x
- Min Deposit: $20
- Valid Days: 30
- Eligible Games: All Slots
- Max Bet: $5
```

**2. Reload Bonus**
- Mevcut oyuncular için
- Haftalık/Aylık
- Daha düşük yüzdeler (25-50%)

**3. Cashback**
- Loss-based cashback
- Percentage: 5-20%
- Weekly/Monthly
- No wagering veya düşük wagering

**4. Free Spins**
- Specific games
- Spin value
- Wagering on winnings
- Expiry period

**5. VIP Reload**
- VIP level bazlı
- Yüksek limitler
- Düşük wagering
- Priority processing

### Bonus Kuralları

#### Wagering Requirements
```
Örnek Hesaplama:
Bonus Amount: $100
Wagering: 35x
Total Wagering Required: $100 x 35 = $3,500

Game Contributions:
- Slots: 100%
- Table Games: 10%
- Live Casino: 10%
- Video Poker: 5%
```

#### Maksimum Bet
Bonus aktifken maksimum bet limiti (örn: $5)

#### Oyun Kısıtlamaları
Belirli oyunlar bonus ile oynanamaz

#### Geçerlilik Süresi
Bonus activation sonrası geçerlilik süresi (örn: 30 gün)

### Kampanya Oluşturma

**Adım Adım:**
```
1. Bonus Management -> "Create Campaign"
2. Campaign Details:
   - Name: "Weekend Reload 50%"
   - Type: Reload Bonus
   - Start Date: Cuma 00:00
   - End Date: Pazar 23:59

3. Bonus Configuration:
   - Percentage: 50%
   - Max Bonus: $200
   - Wagering: 30x
   - Min Deposit: $25

4. Target Audience:
   - All Active Players
   - veya
   - Specific Segment (VIP, Inactive, etc.)
   - Country: Hepsi veya seçili ülkeler

5. Communication:
   - ✅ Email notification
   - ✅ SMS notification
   - ✅ In-app notification
   - Bonus Code: WEEKEND50 (opsiyonel)

6. Preview & Submit
```

### Bonus Onay İşlemleri

**Manuel Bonus Yükleme:**
```
1. Player Management -> Player seç
2. Balance sekmesi -> "Manual Bonus"
3. Form doldur:
   - Bonus Type: Special/Compensation/VIP
   - Amount: $100
   - Wagering: 20x
   - Reason: "VIP birthday bonus"
   - Notes: Internal notes
4. Submit -> Approval Queue
```

---

## Admin Users

### Admin Kullanıcı Yönetimi

#### Roller ve Yetkiler

**Admin Rolleri:**
1. **Super Admin**
   - Tüm yetkilere sahip
   - Config değişiklikleri yapabilir
   - Kill switch kullanabilir

2. **Manager**
   - Çoğu modüle erişim
   - Player management
   - Finance operations
   - Reports

3. **Support**
   - Sadece okuma yetkisi
   - Player support
   - Ticket management

4. **Finance Team**
   - Deposit/Withdrawal approval
   - Financial reports
   - Payment provider management

5. **Fraud Analyst**
   - Risk & Fraud module
   - Player investigation
   - Case management

### Admin Activity Log

**Takip Edilen Aksiyonlar:**
- Player limit değişiklikleri
- Bonus manuel yükleme
- Game RTP değişiklikleri
- Fraud freeze/unfreeze
- Config değişiklikleri
- Withdrawal onayları
- CMS içerik güncellemeleri

**Log Kolonları:**
- Admin ID + Adı
- Action
- Module
- Before / After snapshot
- IP Address
- Timestamp
- Risk Level

**Kullanım:**
```
1. Admin Management -> "Activity Log" sekmesi
2. Filtreleme:
   - Admin seçin
   - Module seçin (Players, Finance, Games, etc.)
   - Action type seçin
   - Tarih aralığı
3. "View Diff" - Değişiklikleri görüntüle
4. "Export Log" - CSV export
```

### Permission Matrix

Rol bazlı izinleri görselleştirir.

**İzin Tipleri:**
- Read - Görüntüleme
- Write - Düzenleme
- Approve - Onaylama
- Export - Veri export
- Restricted - Hassas veri erişimi

**Kullanım:**
```
1. Admin Management -> "Permission Matrix" sekmesi
2. Her rol için modül bazında izinler görünür
3. Edit Permissions butonu (sadece Super Admin)
4. Export Permission Matrix
```

### IP & Device Restrictions

**IP Kısıtlamaları:**
```
Allowed IP (Whitelist):
1. IP & Device sekmesi -> "Add IP"
2. IP Address: 192.168.1.0/24
3. Type: Allowed
4. Reason: "Office network"
5. Submit

Blocked IP (Blacklist):
1. Şüpheli IP tespiti
2. Type: Blocked
3. Reason: "Suspicious login attempts"
```

**Cihaz Yönetimi:**
- Admin ilk defa yeni cihazdan login olduğunda
- Cihaz "Pending" durumuna geçer
- Super Admin onayı gerekir
- Approve edilene kadar erişim kısıtlıdır

### Login History

**Görüntülenen Bilgiler:**
- Admin adı
- Login zamanı
- IP adresi
- Cihaz bilgisi
- Konum
- Sonuç (Başarılı/Başarısız)
- Başarısızlık sebebi

**Şüpheli Giriş Tespiti:**
- ⚠️ Yeni cihaz
- ⚠️ Yeni ülke
- ⚠️ Multiple failed attempts
- ⚠️ Unusual hours

**Kullanım:**
```
1. Admin Management -> "Login History"
2. Filter by:
   - Admin
   - Result (Success/Failed)
   - Suspicious Only
3. Export Login Logs
```

---

## Feature Flags

### Feature Flag Nedir?

Feature flag'ler, yeni özellikleri canlıya almadan önce belirli kullanıcı gruplarında test etmenizi sağlar.

### Flag Oluşturma

```
1. Feature Flags -> "Create Flag"
2. Flag Configuration:
   - Flag ID: new_payment_flow
   - Name: New Payment Flow
   - Description: Yeni ödeme akışı
   - Type: Boolean
   - Default Value: false
   - Scope: Frontend
   - Environment: Production
   - Group: Payments

3. Targeting (Hedefleme):
   - Rollout %: 10% (trafiğin %10'u)
   - Countries: TR, DE (sadece bu ülkeler)
   - VIP Levels: 3, 4, 5 (VIP'ler)
   - Device: mobile/web

4. Create Flag
```

### Flag Yönetimi

**Toggle On/Off:**
```
1. Flag listesinden flag seçin
2. Toggle butonu ile aç/kapa
3. Audit log'a kaydedilir
```

**Targeting Düzenleme:**
```
1. Flag'e tıklayın
2. "Edit Targeting"
3. Rollout % değiştir
4. Ülke listesi güncelle
5. Save
```

**Analytics:**
```
1. Flag seçin
2. "View Analytics"
3. KPI'lar:
   - Activation Rate: %87.5
   - Conversion Impact: +12.3%
   - Error Rate: 0.02%
   - Users Exposed: 45K
```

### A/B Testing

**Experiment Oluşturma:**
```
1. Experiments sekmesi
2. "Create Experiment"

Step 1 - General Info:
- Name: "Deposit Button Color Test"
- Description: "Green vs Blue button"
- Feature Flag: new_deposit_button (opsiyonel)

Step 2 - Variants:
- Variant A (Control): 50% - Mavi buton
- Variant B: 50% - Yeşil buton

Step 3 - Targeting:
- Countries: TR
- New users only: Yes
- VIP: All

Step 4 - Metrics:
- Primary: Conversion Rate
- Secondary: Click-through Rate, Deposit Amount
- Min Sample Size: 5,000

5. Start Experiment
```

**Sonuçları İnceleme:**
```
1. Experiment seçin
2. "View Results"
3. Karşılaştırma:
   - Variant A: 15% conversion
   - Variant B: 18% conversion
   - Statistical Confidence: 95%+
4. "Declare Winner" - B'yi seç
5. Winning variant tüm kullanıcılara açılır
```

### Kill Switch

⚠️ **ACİL DURUM BUTONU**

Tüm feature flag'leri tek tıkla kapatır.

```
Kullanım:
1. Üst sağdaki kırmızı "Kill Switch" butonu
2. Confirmation: "Tüm flag'leri kapatmak istediğinizden emin misiniz?"
3. Yes - Tüm flag'ler OFF durumuna geçer
4. Audit log'a kaydedilir
```

**Ne Zaman Kullanılır:**
- Production'da kritik bug
- Sistem performans sorunu
- Security breach
- Acil rollback gerekli

---

## Simulation Lab

### Game Math Simulator

Oyun matematiğini simüle ederek RTP, volatility ve kazanç dağılımını test edin.

#### Slots Simulator

**Kullanım:**
```
1. Simulation Lab -> "Game Math" sekmesi
2. Slots Simulator

Configuration:
- Game: Big Win Slots seçin
- Spins: 10,000 (Quick test)
  veya 1,000,000 (Production test)
- RTP Override: 96.5%
- Seed: Boş (random) veya belirli seed

3. "Run Simulation" butonuna tıklayın
4. Bekleyin (10K spins ~5 saniye)
```

**Sonuçlar:**
```
Summary Metrics:
- Total Spins: 10,000
- Total Bet: $10,000
- Total Win: $9,652
- Simulated RTP: 96.52%
- Volatility Index: 7.2
- Hit Frequency: 32.5%
- Bonus Hit Frequency: 3.2%
- Max Single Win: $125,000

Win Distribution:
- 0x (No win): 4,500 spins (45%)
- 0-1x: 3,200 spins (32%)
- 1-10x: 1,800 spins (18%)
- 10-50x: 400 spins (4%)
- 50-100x: 80 spins (0.8%)
- 100x+: 20 spins (0.2%)
```

**Export:**
- 📊 Show Graphs - Görsel grafikler
- 📄 Export CSV - İlk 10,000 spin
- 📁 Download Bundle (ZIP) - Tüm konfigürasyon + sonuçlar

#### Table Games Simulator

Blackjack, Roulette, Baccarat simülasyonu.

**Blackjack Örnek:**
```
1. Table / Live Simulator sekmesi
2. Game Type: Blackjack
3. Rules: Standard (3:2, dealer stands on 17)
4. Rounds: 10,000
5. Player Strategy: Basic Strategy
6. Run Simulation

Sonuçlar:
- House Edge: 0.5%
- RTP: 99.5%
- Average Session: -$50 (1000 rounds)
- Bust Rate: 28%
- Blackjack Rate: 4.8%
```

### Portfolio Simulator

Oyun portföyünüzde RTP ve traffic değişikliklerinin revenue etkisini simüle edin.

**Kullanım:**
```
1. Portfolio sekmesi
2. "Import from Live Data" - Mevcut oyun trafiği

Game List:
Game A: Current RTP 96%, Traffic 30% -> New RTP 95%, Traffic 35%
Game B: Current RTP 97%, Traffic 25% -> New RTP 97%, Traffic 20%
Game C: Current RTP 94%, Traffic 20% -> New RTP 95%, Traffic 25%

3. "Run Portfolio Simulation"

Results:
- Current GGR: $1,250,000
- Simulated GGR: $1,315,000 (+5.2%)
- Current NGR: $1,062,500
- Simulated NGR: $1,117,750 (+5.2%)
- Jackpot Cost: -$26,300
- Bonus Cost: -$65,750
```

### Bonus Simulator

Bonus parametrelerinin ekonomik etkisini test edin.

**Örnek Senaryo:**
```
Mevcut Welcome Bonus: 100%, 35x wagering
Yeni Teklif: 150%, 40x wagering

Configuration:
- Bonus Type: Welcome
- Current %: 100
- New %: 150
- Current Wagering: 35x
- New Wagering: 40x
- Expected Participants: 1,000
- Avg Deposit: $100

Run Simulation

Results:
- Total Bonus Issued: $150,000
- Bonus Used: $112,500 (75%)
- Liabilities: $4,500,000 (wagering req)
- Additional GGR: $675,000
- Net Cost: -$112,500
- Additional GGR - Cost: +$562,500
- ROI: 400%
- Expected Abuse Rate: 5%
- Fraud Flags: 12
```

### Cohort / LTV Simulator

Oyuncu segmentlerinin Lifetime Value simülasyonu.

**Kullanım:**
```
1. Cohort/LTV sekmesi
2. Segment: VIP Players seçin
3. Time Horizon: 90 days
4. Baseline LTV: $850 (mevcut data'dan)

Policy Changes:
- ✅ Increase welcome bonus 100% -> 150%
- ✅ Increase reload bonus frequency
- ⬜ Reduce cashback
- ⬜ Change RG limits

Run Simulation

Results:
- Baseline LTV: $850
- Simulated LTV: $977.5 (+15%)
- Deposit Frequency: 5.2
- Churn Rate: 22%
- Bonus Cost: $117.30
- RG Flag Rate: 4.2%
- Fraud Risk Impact: 1.8%
```

### Risk Simulator

Risk kurallarının değişiminin etkisini test edin.

**Senaryo:**
```
Risk Rule: Device Fingerprint Mismatch
Current Threshold: 3 mismatches -> Flag
Proposed Threshold: 2 mismatches -> Flag

Time Window: Last 30 days replay

Run Risk Simulation

Results:
- Total Alerts (Current): 1,245
- Total Alerts (Simulated): 1,623 (+30%)
- Fraud Caught: 243 (+15%)
- False Positives: 406 (+35%)
- Auto-Freeze Count: 146
- Withdrawal Blocks: 97
- Lost Revenue (false positives): -$20,300
```

### Archive

Tüm simülasyonlar arşivlenir.

**Kullanım:**
```
1. Archive sekmesi
2. Simulation listesi:
   - ID, Name, Type, Status, Owner, Tags
3. Actions:
   - 🔍 Open Result - Sonuçları görüntüle
   - ▶️ Rerun - Güncel data ile tekrar çalıştır
   - 📄 Export - Config + Results export
   - 🗑️ Delete
```

---

## Settings Panel

### Brand Management

Multi-brand operasyonlar için brand yönetimi.

**Yeni Brand Ekleme:**
```
1. Settings -> Brands sekmesi
2. "Add Brand" butonu

Form:
- Brand Name: Super777
- Default Currency: EUR
- Default Language: en
- Domains: super777.com, www.super777.com
- Languages Supported: en, es, pt
- Logo Upload: (dosya seçin)
- Favicon Upload: (dosya seçin)
- Contact Info:
  - Support Email: support@super777.com
  - Support Phone: +1-555-0123
- Timezone: UTC+1
- Country Availability: ES, PT, BR

3. "Create" butonu
```

**Brand Düzenleme:**
- Edit butonu ile tüm ayarlar değiştirilebilir
- Domain ekleme/çıkarma
- Logo güncelleme
- Country list düzenleme

### Currency Management

Para birimleri ve döviz kurları.

**Görüntülenen Bilgiler:**
- Currency Code (USD, EUR, TRY, GBP)
- Symbol ($, €, ₺, £)
- Exchange Rate (Base: USD = 1.0)
- Min/Max Deposit
- Min/Max Bet

**Döviz Kurlarını Güncelleme:**
```
1. Currencies sekmesi
2. "Sync Rates" butonu
3. External API'den güncel kurlar çekilir
4. Otomatik update
```

**Yeni Currency Ekleme:**
```
1. "Add Currency"
2. Form:
   - Code: BRL
   - Symbol: R$
   - Exchange Rate: 5.25 (USD bazlı)
   - Rounding: 2 decimal places
   - Min Deposit: $10 equivalent
   - Max Deposit: $10,000 equivalent
3. Create
```

### Country Rules

Ülke bazlı kısıtlamalar ve kurallar.

**Kolonlar:**
- Country Name & Code
- Allowed (Yes/No)
- Games Allowed
- Bonuses Allowed
- KYC Level (1, 2, 3)
- Payment Restrictions

**Örnek Kurallar:**
```
Turkey (TR):
- Allowed: Yes
- Games: Yes
- Bonuses: Yes
- KYC Level: 2 (ID + Proof of Address)
- Payment Methods: All except Bitcoin

China (CN):
- Allowed: No
- Games: No
- Bonuses: No
- KYC Level: N/A
- Geo-blocking: Active
```

**Kural Düzenleme:**
```
1. Country seçin
2. "Edit Country Rules"
3. Değişiklikler:
   - KYC level artır/azalt
   - Payment method ekle/çıkar
   - Bonus eligibility değiştir
4. Save
```

### Payment Provider Settings

Ödeme sağlayıcıları konfigürasyonu.

**Provider Ekleme:**
```
1. Payment sekmesi
2. "Add Provider"

Form:
- Provider Name: Stripe
- Type: Deposit & Withdrawal
- API Keys: 
  - Public Key: pk_live_xxx (masked)
  - Secret Key: sk_live_xxx (masked)
- Availability: TR, US, UK, DE
- Min Amount: $10
- Max Amount: $10,000
- Fees:
  - Deposit: 2.5%
  - Withdrawal: 1.5%
- Currency Support: USD, EUR, TRY

3. "Run Health Check" - API bağlantısını test et
4. Save
```

**Health Check:**
- API connectivity
- Balance check (provider side)
- Transaction processing capability
- Webhook functionality

### Platform Defaults

Global sistem varsayılanları.

**Ayarlar:**
```
- Default Language: en
- Default Currency: USD
- Default Timezone: UTC
- Session Timeout: 30 minutes
- Password Min Length: 8 characters
- Require 2FA: No (opsiyonel)
- Cache TTL: 300 seconds
- Pagination: 20 items per page
- API Rate Limit: 60 requests/minute
```

**Değiştirme:**
```
1. Defaults sekmesi
2. Değerleri düzenleyin
3. "Save Defaults"
4. Sistem geneline uygulanır
```

### API Key Management

API anahtarları ve webhook yönetimi.

**API Key Oluşturma:**
```
1. API Keys sekmesi
2. "Generate Key"

Form:
- Key Name: Production API
- Owner: Brand/System
- Permissions:
  - ✅ Read
  - ✅ Write
  - ⬜ Delete
  - ✅ Admin

3. Generate

Response:
API Key: sk_live_abc123xyz456... (TEK SEFER GÖSTER)
Key ID: key_789

⚠️ API key'i güvenli bir yerde saklayın!
```

**API Key Revoke:**
```
1. Key listesinden seçin
2. "Revoke" butonu
3. Confirm
4. Key deactive edilir, kullanılamaz
```

**Webhook Ekleme:**
```
1. API Keys sekmesi -> Webhooks bölümü
2. "Add Webhook"

Form:
- Event Type: player.deposit.completed
- Endpoint URL: https://yourapi.com/webhooks/deposit
- Secret Token: (auto-generated)
- Retry Policy:
  - Max Retries: 3
  - Backoff: Exponential

3. "Send Test Event" - Webhook'u test et
4. Save
```

### Maintenance Scheduling

Bakım penceresi planlama.

**Maintenance Oluşturma:**
```
1. Maintenance sekmesi
2. "Schedule Maintenance"

Form:
- Brand: CasinoX
- Type: Full Site / Games Only / Payments Only
- Start Time: 2024-01-15 02:00 UTC
- End Time: 2024-01-15 04:00 UTC
- Message (Multilingual):
  - EN: "Scheduled maintenance. We'll be back soon!"
  - TR: "Planlı bakım. Yakında döneceğiz!"
- Affecting: [x] Entire Site

3. Schedule

User'lara notification gönderilir
Scheduled time'da otomatik maintenance mode aktif olur
```

**Erken Bitirme:**
```
1. Active maintenance seçin
2. "End Maintenance Early" butonu
3. Confirm
4. Site yeniden açılır
```

### Config Versions

Konfigürasyon versiyonlama ve deployment.

**Version Oluşturma:**
```
1. Versions sekmesi
2. "Create Version"

Form:
- Version Number: v2.1.5
- Environment: Staging
- Change Summary: "RTP updates for 15 games"
- Config Snapshot: (otomatik)

3. "Save Draft"
```

**Deployment:**
```
Draft -> Staging:
1. Version seçin
2. "Publish to Staging"
3. Staging environment'a deploy edilir
4. Test edin

Staging -> Production:
1. Test tamamlandıysa
2. "Deploy to Production"
3. Approval gerekir (dual-control)
4. Approved -> Production'a deploy

Rollback:
1. Version seçin
2. "Rollback Version"
3. Önceki versiyona geri dön
```

---

## Risk & Fraud Management

### Risk Rules Engine

Kural bazlı fraud detection sistemi.

**Kural Kategorileri:**
1. **Payment Rules** - Ödeme fraud'u
2. **Device Rules** - Cihaz tabanlı
3. **Bonus Abuse Rules** - Bonus kötüye kullanımı
4. **Account Rules** - Hesap anomalileri

**Örnek Kurallar:**
```
Rule: Multiple Accounts from Same Device
- Trigger: 3+ accounts, same device fingerprint
- Action: Flag + Manual Review
- Weight: 30 points

Rule: Velocity Check
- Trigger: 5+ deposits in 1 hour
- Action: Auto-block + Notification
- Weight: 50 points

Rule: Geo Mismatch
- Trigger: IP country ≠ Registration country
- Action: Flag + KYC verification
- Weight: 20 points
```

### Risk Cases

Şüpheli aktivite case'leri.

**Case Workflow:**
```
1. Otomatik tespit (Risk Engine)
2. Case oluşturulur (Status: Open)
3. Fraud Analyst'e assign edilir
4. Investigation:
   - Player profile review
   - Transaction analysis
   - Device/IP check
   - Communication history
5. Decision:
   - False Positive -> Close
   - True Fraud -> Block + Report
   - Suspicious -> Monitor
6. Case kapatılır
```

**Case Detayları:**
- Player ID
- Risk Score (0-100)
- Triggered Rules
- Evidence (screenshots, logs)
- Investigation Notes
- Resolution
- Assigned To
- Status

### Device Intelligence

Cihaz fingerprinting ve analiz.

**Toplanan Bilgiler:**
- Browser fingerprint
- Screen resolution
- Timezone
- Language
- Plugins
- WebGL info
- Canvas fingerprint

**Kullanım:**
```
Multi-account detection:
1. Player A, Device X
2. Player B, Device X (Same fingerprint!)
3. Alert: Possible multi-accounting
4. Manual review

VPN Detection:
1. IP mismatch with timezone
2. IP in VPN database
3. Flag: VPN usage
```

### Payment Risk

Ödeme fraud tespiti.

**Risk Faktörleri:**
- Yüksek değerli ilk deposit
- Rapid succession deposits
- Payment method hopping
- Chargeback history
- Stolen card indicators

**Önlemler:**
```
High Risk Payment:
1. 3D Secure required
2. Lower transaction limit
3. Extended processing time
4. Additional KYC documents
```

---

## Reports

### Financial Reports

**Daily Revenue Report:**
```
Date Range: Last 7 days
Breakdown:
- GGR by day
- NGR by day
- Deposit count & amount
- Withdrawal count & amount
- Bonus cost
- Net revenue

By Provider:
- Pragmatic Play: $125,000 GGR
- Evolution Gaming: $95,000 GGR
- NetEnt: $78,000 GGR

By Game Category:
- Slots: 65%
- Live Casino: 25%
- Table Games: 10%
```

**Player Reports:**
```
Player Activity Report:
- New registrations
- Active players
- Churned players
- Reactivations
- Average session time
- ARPU (Average Revenue Per User)

Segmentation:
- By VIP level
- By country
- By acquisition channel
```

**Bonus Reports:**
```
Bonus Performance:
- Total issued: $50,000
- Total used: $37,500 (75%)
- Wagering completed: $28,125 (56%)
- ROI: 180%
- Abuse cases: 12

By Bonus Type:
- Welcome: 45%
- Reload: 30%
- Cashback: 15%
- Free Spins: 10%
```

### Operational Reports

**Game Performance:**
```
Top 10 Games by Revenue:
1. Sweet Bonanza - $45,000
2. Gates of Olympus - $38,000
3. Book of Dead - $32,000
...

RTP Analysis:
- Configured RTP: 96.5%
- Actual RTP: 96.48%
- Variance: -0.02% (normal)

Game Issues:
- Downtime: 0.05%
- Error rate: 0.02%
- Player complaints: 3
```

**Payment Provider Report:**
```
Provider Performance:
Stripe:
- Success Rate: 98.5%
- Avg Processing Time: 1.2 seconds
- Total Volume: $1.2M

PayPal:
- Success Rate: 97.8%
- Avg Processing Time: 2.5 seconds
- Total Volume: $850K

Failed Transactions Analysis:
- Insufficient Funds: 45%
- Card Expired: 25%
- Fraud Check Failed: 20%
- Technical Error: 10%
```

### Compliance Reports

**AML Report:**
```
High Value Transactions (>$10,000):
- Count: 45
- Reviewed: 45
- Flagged: 3
- Reported: 1

PEP Checks:
- Players Screened: 1,250
- PEP Matches: 2
- Enhanced Due Diligence: 2
```

**RG Report:**
```
Responsible Gaming:
- Limit Settings: 340 players
- Self-Exclusions: 12 players
- Reality Checks Triggered: 1,200
- Cooling-Off Periods: 8

Intervention Success:
- Players Responded: 78%
- Limit Adjustments: 45%
- Support Contact: 22%
```

---

## Best Practices

### Güvenlik
1. ✅ 2FA her admin için aktif olmalı
2. ✅ IP whitelist kullanın
3. ✅ API key'leri düzenli rotate edin
4. ✅ Sensitive data loglarında mask edin
5. ✅ Regular security audits

### Operasyonel
1. ✅ Daily reports gözden geçirin
2. ✅ Withdrawal queue'yu günde 2-3 kez kontrol edin
3. ✅ Risk cases'leri 24 saat içinde çözün
4. ✅ Player complaints hızlı yanıtlayın
5. ✅ Regular backup alın

### Testing
1. ✅ Yeni oyunları Simulation Lab'de test edin
2. ✅ RTP değişikliklerini simüle edin
3. ✅ Feature flag'leri %10 ile başlatın
4. ✅ A/B testleri minimum 5K sample size
5. ✅ Bonus ROI'yi sürekli monitor edin

### Compliance
1. ✅ KYC verification'ları güncel tutun
2. ✅ AML threshold'ları düzenli review edin
3. ✅ License requirement'larını takip edin
4. ✅ RG tools'u oyunculara tanıtın
5. ✅ Audit logs'u preserve edin

---

## Troubleshooting

### Sık Karşılaşılan Sorunlar

**Problem: Withdrawal onaylanamıyor**
```
Çözüm:
1. Player KYC durumunu kontrol edin
2. Wagering requirement karşılandı mı?
3. Duplicate withdrawal check yapın
4. Risk engine sonuçlarına bakın
5. Manuel review gerekiyorsa assign edin
```

**Problem: Game RTP beklenenin altında**
```
Çözüm:
1. Sample size yeterli mi? (min 100K spins)
2. Paytable konfigürasyonunu kontrol edin
3. Simulation Lab'de test edin
4. Provider ile iletişime geçin
5. Game version'u kontrol edin
```

**Problem: Bonus abuse şüphesi**
```
Çözüm:
1. Player'ın tüm accountlarını kontrol edin
2. Device fingerprint check
3. IP history
4. Betting patterns analiz edin
5. Risk case oluşturun
```

**Problem: Feature flag hatalı çalışıyor**
```
Çözüm:
1. Targeting rules'u kontrol edin
2. Environment doğru mu? (prod/staging)
3. Kill switch kullanın (acil durum)
4. Rollback yapın
5. Developer ile iletişime geçin
```

### Destek

**İletişim:**
- Technical Support: tech@casinoadmin.com
- Security Issues: security@casinoadmin.com
- Emergency: +1-555-EMERGENCY

**Dokümantasyon:**
- API Docs: /api/docs
- Changelog: /changelog
- Release Notes: /releases

---

## Klavye Kısayolları

- `Ctrl+K` - Global arama
- `Ctrl+/` - Komut paleti
- `Ctrl+R` - Refresh data
- `Ctrl+E` - Export current view
- `Esc` - Close modal/dialog

---

## Sürüm Bilgisi

**Versiyon:** 2.0.0
**Son Güncelleme:** Aralık 2024
**Platform:** FastAPI + React + MongoDB

---

**💡 İpucu:** Bu kılavuz düzenli olarak güncellenmektedir. En son versiyonu `/docs` adresinden kontrol edin.
