# 🎰 Casino Yönetici Paneli - Kapsamlı Kullanım Kılavuzu

## 📋 İçindekiler

1. [Genel Bakış](#overview)
2. [Gösterge Paneli](#dashboard)
3. [Oyuncu Yönetimi](#player-management)
4. [Oyun Yönetimi](#game-management)
5. [Finans Yönetimi](#finance-management)
6. [Bonus Yönetimi](#bonus-management)
7. [Yönetici Kullanıcılar](#admin-users)
8. [Özellik Bayrakları & A/B Testi](#feature-flags)
9. [Simülasyon Laboratuvarı](#simulation-lab)
10. [Ayarlar Paneli](#settings-panel)
11. [Risk & Dolandırıcılık Yönetimi](#risk-fraud)
12. [Raporlar](#reports)

---

## Genel Bakış

Casino Yönetici Paneli, casino operatörleri için tasarlanmış kurumsal düzeyde bir yönetim platformudur. Oyuncu yönetiminden oyun yapılandırmasına, bonus sistemlerinden risk yönetimine kadar tüm casino operasyonlarını tek bir yerden yönetin.

### Temel Özellikler
- 🎮 **Kapsamlı Oyun Yönetimi** - RTP ayarları, VIP masaları, özel masalar
- 👥 **Detaylı Oyuncu Profilleri** - KYC, bakiye, oyun geçmişi, loglar
- 💰 **Finans Modülü** - Para yatırma/çekme yönetimi, raporlar
- 🎁 **Gelişmiş Bonus Sistemi** - Şablonlar, kurallar, kampanyalar
- 🛡️ **Risk & Dolandırıcılık Yönetimi** - Yapay zekâ destekli dolandırıcılık tespiti
- 🧪 **Simülasyon Laboratuvarı** - Oyun matematiği ve gelir simülasyonları
- 🏢 **Çok Kiracılı (Multi-Tenant)** - Çoklu marka yönetimi

### Sistem Gereksinimleri
- Modern web tarayıcısı (Chrome, Firefox, Safari, Edge)
- Minimum 1920x1080 çözünürlük önerilir
- İnternet bağlantısı

---

## Gösterge Paneli

### Genel Bakış
Gösterge Paneli, casino operasyonlarınızın gerçek zamanlı durumunu gösterir.

### Ana KPI'lar
1. **GGR (Brüt Oyun Geliri)** - Toplam oyun geliri
2. **NGR (Net Oyun Geliri)** - Net oyun geliri
3. **Aktif Oyuncular** - Aktif oyuncu sayısı
4. **Para Yatırma Sayısı** - Toplam para yatırma işlemleri
5. **Para Çekme Sayısı** - Toplam para çekme işlemleri

### Grafikler
- **Gelir Trendi** - Son 7 gün gelir trendi
- **Oyuncu Aktivitesi** - Oyuncu aktivite grafiği
- **En Popüler Oyunlar** - En çok oynanan oyunlar
- **Ödeme Durumu** - Ödeme durumları

### Kullanım
1. Sol menüden "Dashboard" seçin
2. Tarih aralığını değiştirmek için tarih seçiciyi kullanın
3. Detaylı rapor için herhangi bir KPI kartına tıklayın
4. Verileri güncellemek için "Refresh" düğmesini kullanın

---

## Oyuncu Yönetimi

### Oyuncu Listesi

#### Filtreleme
Oyuncuları şunlara göre filtreleyin:
1. **Arama Çubuğu** - E-posta, kullanıcı adı veya oyuncu ID ile arayın
2. **Durum Filtresi** - Aktif, Askıya Alındı, Engellendi
3. **VIP Seviyesi** - VIP seviyesine göre filtreleyin
4. **Kayıt Tarihi** - Kayıt tarihine göre filtreleyin

#### Sıralama
- Oyuncu ID
- Kullanıcı adı
- Kayıt Tarihi
- Toplam Para Yatırma
- Son Giriş

#### Toplu İşlemler
- **Toplu Askıya Alma** - Seçili oyuncuları askıya alın
- **Toplu Dışa Aktarma** - Excel/CSV'ye dışa aktarın
- **Toplu Mesaj Gönderme** - Seçili oyunculara mesaj gönderin

### Oyuncu Detay Sayfası

#### Sekmeler

**1. Profil**
- Temel bilgiler (Ad, e-posta, telefon)
- VIP seviyesi
- Kayıt tarihi
- Son giriş
- Durum (Aktif/Askıya Alındı/Engellendi)

**Eylemler:**
- ✏️ Profili Düzenle
- 🚫 Oyuncuyu Askıya Al
- ⛔ Oyuncuyu Engelle
- 📧 E-posta Gönder

**2. KYC (Kimlik Doğrulama)**
- KYC seviyesi (Seviye 1, 2, 3)
- Yüklenen belgeler
- Doğrulama durumu
- Doğrulama notları

**Eylemler:**
- ✅ Belgeyi Onayla
- ❌ Belgeyi Reddet
- 📤 Ek Belgeler Talep Et

**3. Bakiye**
- Gerçek Para Bakiyesi
- Bonus Bakiyesi
- Kilitli Bakiye
- Toplam Çevrim
- Bekleyen Para Çekme İşlemleri

**Eylemler:**
- ➕ Manuel Alacak Tanımla
- ➖ Manuel Borçlandır
- 🔒 Bakiyeyi Kilitle
- 📊 İşlem Geçmişini Görüntüle

**4. Oyun Geçmişi**
- Oynanan oyunların listesi
- Bahis tutarları
- Kazanç/Kayıp durumu
- RTP gerçekleşmeleri
- Son 100 oturum

**Filtreleme:**
- Tarih aralığı
- Oyun türü
- Sağlayıcı
- Kazanç/Kayıp

**5. İşlem Kaydı**
- Tüm finansal işlemler
- Para yatırma
- Para çekme
- Bonuslar
- Manuel düzeltmeler

**6. Aktivite Kaydı**
- Giriş/çıkış kayıtları
- IP adresleri
- Cihaz bilgileri
- Şüpheli aktiviteler

---

## Oyun Yönetimi

### Oyun Listesi

#### Genel Ayarlar
Her oyun için:
- **Durum** - Aktif/Pasif
- **RTP** - Oyuncuya İade yüzdesi
- **Min/Max Bet** - Minimum ve maksimum bahis limitleri
- **Volatilite** - Oyun volatilitesi
- **Hit Frequency** - Kazanma sıklığı

#### RTP Yönetimi

**RTP Profilleri:**
1. Standart (96.5%)
2. Yüksek (97.5%)
3. VIP (98%)
4. Özel

**RTP Değiştirme:**```
1. Select game
2. Click "Edit Game"
3. Go to "RTP Configuration" tab
4. Enter new RTP value
5. "Save Draft" -> Sent to Approval Queue
6. Active after Super Admin approval
```⚠️ **Önemli:** RTP değişiklikleri çift kontrol sisteminden geçer.

### VIP & Özel Masalar

#### VIP Masası Oluşturma```
1. "Game Management" -> "VIP Games" tab
2. Click "Create VIP Table"
3. Fill form:
   - Table Name
   - Base Game ID
   - Min Bet (e.g., $100)
   - Max Bet (e.g., $10,000)
   - VIP Level Requirement (e.g., Level 3)
   - Max Players
   - Special Features (optional)
4. Click "Create"
```**VIP Masa Özellikleri:**
- Yüksek bahis limitleri
- Özel RTP profilleri
- Özel oda seçeneği
- Özel krupiye (canlı oyunlar için)
- Özel bonuslar

### Ödeme Tablosu Yönetimi

Slot oyunları için sembol ağırlıkları ve ödeme tablosu yapılandırması:```
1. Select game
2. Click "Paytable Config"
3. For each symbol:
   - Reel weights (weight for each reel)
   - Payout values
   - Scatter/Wild configuration
4. "Save & Validate" - Automatic RTP calculation
5. "Submit for Approval"
```### Jackpot Yapılandırması

**Jackpot Türleri:**
1. **Sabit Jackpot** - Sabit jackpot
2. **Progresif Jackpot** - Progresif jackpot
3. **Çok Seviyeli Jackpot** - Mini, Minor, Major, Grand

**Ayarlar:**
- Seed Amount - Başlangıç tutarı
- Contribution % - Her bahisten jackpot’a aktarılan yüzde
- Win Probability - Kazanma olasılığı
- Max Cap - Maksimum limit

---

## Finans Yönetimi

### Para Yatırma Yönetimi

#### Para Yatırma Talepleri
Bekleyen para yatırma taleplerini görüntüleyin:

**Sütunlar:**
- Oyuncu ID/Kullanıcı adı
- Tutar
- Ödeme Yöntemi
- Durum (Beklemede, Onaylandı, Reddedildi)
- Talep Zamanı
- İşlem Süresi

**Eylemler:**
1. **Onayla** - Para yatırmayı onaylayın
   - Otomatik olarak oyuncu bakiyesine eklenir
   - İşlem kaydı oluşturulur
   - Oyuncuya e-posta gönderilir

2. **Reddet** - Para yatırmayı reddedin
   - Reddetme nedenini seçin
   - Oyuncuya bildirim gönderilir

3. **Şüpheli Olarak İşaretle** - Şüpheli olarak işaretleyin
   - Risk motoruna gönderilir
   - Manuel inceleme gerektirir

### Para Çekme Yönetimi

#### Para Çekme Talepleri

**Onay Süreci:**```
1. Check Pending Withdrawals list
2. Review player profile
3. Check KYC status
4. Review recent activity
5. Check fraud check results
6. Approve or Reject
```**Otomatik Kontroller:**
- ✅ KYC Seviyesi kontrolü
- ✅ Çevrim (wagering) şartı karşılandı mı?
- ✅ Çift (duplicate) para çekme kontrolü
- ✅ Hız (velocity) kontrolü
- ✅ Cihaz parmak izi eşleşmesi
- ✅ IP konumu eşleşmesi

**Reddetme Nedenleri:**
- KYC tamamlanmadı
- Çevrim (wagering) şartı karşılanmadı
- Şüpheli aktivite
- Belge doğrulaması gerekli
- Çift hesap şüphesi

### Finansal Raporlar

#### Rapor Türleri

**1. Günlük Gelir Raporu**
- GGR/NGR kırılımı
- Oyun sağlayıcısına göre
- Oyun kategorisine göre
- Oyuncu segmentine göre

**2. Para Yatırma/Para Çekme Raporu**
- Başarı oranları
- Ortalama tutarlar
- Ödeme yöntemine göre
- İşlem süreleri

**3. Bonus Maliyet Raporu**
- Verilen toplam bonus
- Kullanılan bonus
- Tamamlanan çevrim (wagering)
- ROI analizi

**Dışa Aktarma Seçenekleri:**
- 📄 PDF
- 📊 Excel
- 📋 CSV
- 📧 E-posta Zamanlaması (günlük/haftalık)

---

## Bonus Yönetimi

### Bonus Şablonları

#### Bonus Türleri

**1. Hoş Geldin Bonusu**```yaml
Example Configuration:
- Type: Deposit Match
- Percentage: 100%
- Max Amount: $500
- Wagering: 35x
- Min Deposit: $20
- Valid Days: 30
- Eligible Games: All Slots
- Max Bet: $5
```**2. Yeniden Yükleme Bonusu**
- Mevcut oyuncular için
- Haftalık/Aylık
- Daha düşük yüzdeler (25-50%)

**3. Nakit İade (Cashback)**
- Kayıp bazlı nakit iade
- Yüzde: 5-20%
- Haftalık/Aylık
- Çevrim yok veya düşük çevrim

**4. Ücretsiz Spinler**
- Belirli oyunlar
- Spin değeri
- Kazançlar üzerinde çevrim
- Son kullanma süresi

**5. VIP Yeniden Yükleme**
- VIP seviyesine göre
- Daha yüksek limitler
- Daha düşük çevrim
- Öncelikli işleme

### Bonus Kuralları

#### Çevrim (Wagering) Gereksinimleri```
Example Calculation:
Bonus Amount: $100
Wagering: 35x
Total Wagering Required: $100 x 35 = $3,500

Game Contributions:
- Slots: 100%
- Table Games: 10%
- Live Casino: 10%
- Video Poker: 5%
```#### Maksimum Bahis
Bonus aktifken maksimum bahis limiti (örn. $5)

#### Oyun Kısıtlamaları
Bazı oyunlar bonus ile oynanamaz

#### Geçerlilik Süresi
Bonus aktivasyonundan sonraki geçerlilik süresi (örn. 30 gün)

### Kampanya Oluşturma

**Adım Adım:**```
1. Bonus Management -> "Create Campaign"
2. Campaign Details:
   - Name: "Weekend Reload 50%"
   - Type: Reload Bonus
   - Start Date: Friday 00:00
   - End Date: Sunday 23:59

3. Bonus Configuration:
   - Percentage: 50%
   - Max Bonus: $200
   - Wagering: 30x
   - Min Deposit: $25

4. Target Audience:
   - All Active Players
   - or
   - Specific Segment (VIP, Inactive, etc.)
   - Country: All or selected countries

5. Communication:
   - ✅ Email notification
   - ✅ SMS notification
   - ✅ In-app notification
   - Bonus Code: WEEKEND50 (optional)

6. Preview & Submit
```---

## Yönetici Kullanıcılar

### Yönetici Kullanıcı Yönetimi

#### Roller ve Yetkiler

**Yönetici Rolleri:**
1. **Süper Yönetici** - Her şeye tam erişim
2. **Yönetici** - Çoğu modüle erişim
3. **Destek** - Salt okunur erişim
4. **Finans Ekibi** - Para yatırma/çekme onayı
5. **Dolandırıcılık Analisti** - Risk & dolandırıcılık modülü

### Yönetici Aktivite Kaydı

**Takip Edilen İşlemler:**
- Oyuncu limit değişiklikleri
- Manuel bonus yükleme
- Oyun RTP değişiklikleri
- Dolandırıcılık dondurma/çözme
- Yapılandırma değişiklikleri
- Para çekme onayları
- CMS içerik güncellemeleri

**Log Sütunları:**
- Yönetici ID + Ad
- İşlem
- Modül
- Önce / Sonra anlık görüntüsü
- IP Adresi
- Zaman damgası
- Risk Seviyesi

**Kullanım:**```
1. Admin Management -> "Activity Log" tab
2. Filter:
   - Select admin
   - Select module (Players, Finance, Games, etc.)
   - Select action type
   - Date range
3. "View Diff" - View changes
4. "Export Log" - CSV export
```### Yetki Matrisi

Rol bazlı yetkileri görselleştirir.

**Yetki Türleri:**
- Read - Görüntüleme
- Write - Düzenleme
- Approve - Onaylama
- Export - Veri dışa aktarma
- Restricted - Hassas verilere erişim

### IP & Cihaz Kısıtlamaları

**IP Kısıtlamaları:**```
Allowed IP (Whitelist):
1. IP & Device tab -> "Add IP"
2. IP Address: 192.168.1.0/24
3. Type: Allowed
4. Reason: "Office network"
5. Submit

Blocked IP (Blacklist):
1. Suspicious IP detected
2. Type: Blocked
3. Reason: "Suspicious login attempts"
```**Cihaz Yönetimi:**
- Yönetici yeni bir cihazdan giriş yaptığında
- Cihaz "Pending" durumuna alınır
- Süper Yönetici onayı gerekir
- Onaylanana kadar erişim kısıtlanır

### Giriş Geçmişi

**Görüntülenen Bilgiler:**
- Yönetici adı
- Giriş zamanı
- IP adresi
- Cihaz bilgileri
- Konum
- Sonuç (Başarılı/Başarısız)
- Başarısızlık nedeni

**Şüpheli Giriş Tespiti:**
- ⚠️ Yeni cihaz
- ⚠️ Yeni ülke
- ⚠️ Birden fazla başarısız deneme
- ⚠️ Olağandışı saatler

---

## Feature Flags

### Feature Flag Nedir?

Feature flag’ler, yeni özellikleri tam yayına almadan önce belirli kullanıcı gruplarında test etmenizi sağlar.

### Flag Oluşturma```
1. Feature Flags -> "Create Flag"
2. Flag Configuration:
   - Flag ID: new_payment_flow
   - Name: New Payment Flow
   - Description: New payment flow
   - Type: Boolean
   - Default Value: false
   - Scope: Frontend
   - Environment: Production
   - Group: Payments

3. Targeting:
   - Rollout %: 10% (10% of traffic)
   - Countries: TR, DE (only these countries)
   - VIP Levels: 3, 4, 5 (VIPs only)
   - Device: mobile/web

4. Create Flag
```### Flag Yönetimi

**Aç/Kapat (Toggle):**```
1. Select flag from list
2. Use toggle button to on/off
3. Recorded in audit log
```**Hedeflemeyi Düzenle:**```
1. Click on flag
2. "Edit Targeting"
3. Change rollout %
4. Update country list
5. Save
```**Analitik:**```
1. Select flag
2. "View Analytics"
3. KPIs:
   - Activation Rate: 87.5%
   - Conversion Impact: +12.3%
   - Error Rate: 0.02%
   - Users Exposed: 45K
```### A/B Testi

**Deney Oluşturma:**```
1. Experiments tab
2. "Create Experiment"

Step 1 - General Info:
- Name: "Deposit Button Color Test"
- Description: "Green vs Blue button"
- Feature Flag: new_deposit_button (optional)

Step 2 - Variants:
- Variant A (Control): 50% - Blue button
- Variant B: 50% - Green button

Step 3 - Targeting:
- Countries: TR
- New users only: Yes
- VIP: All

Step 4 - Metrics:
- Primary: Conversion Rate
- Secondary: Click-through Rate, Deposit Amount
- Min Sample Size: 5,000

5. Start Experiment
```### Kill Switch

⚠️ **ACİL DURUM DÜĞMESİ**

Tüm feature flag’leri tek tıklamayla kapatır.```
Usage:
1. Red "Kill Switch" button at top right
2. Confirmation: "Are you sure you want to disable all flags?"
3. Yes - All flags go to OFF status
4. Recorded in audit log
```**Ne Zaman Kullanılır:**
- Prodüksiyonda kritik hata
- Sistem performans sorunu
- Güvenlik ihlali
- Acil rollback gerekiyor

---

## Simülasyon Laboratuvarı

### Oyun Matematiği Simülatörü

RTP, volatilite ve kazanç dağılımını test etmek için oyun matematiğini simüle edin.

#### Slot Simülatörü

**Kullanım:**```
1. Simulation Lab -> "Game Math" tab
2. Slots Simulator

Configuration:
- Game: Select Big Win Slots
- Spins: 10,000 (Quick test)
  or 1,000,000 (Production test)
- RTP Override: 96.5%
- Seed: Empty (random) or specific seed

3. Click "Run Simulation"
4. Wait (10K spins ~5 seconds)
```**Sonuçlar:**```
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
```**Dışa Aktarma:**
- 📊 Show Graphs - Görsel grafikler
- 📄 Export CSV - İlk 10.000 spin
- 📁 Download Bundle (ZIP) - Tüm konfigürasyon + sonuçlar

---

## Ayarlar Paneli

### Marka Yönetimi

Çoklu marka operasyonları için marka yönetimi.

**Yeni Marka Ekleme:**```
1. Settings -> Brands tab
2. "Add Brand" button

Form:
- Brand Name: Super777
- Default Currency: EUR
- Default Language: en
- Domains: super777.com, www.super777.com
- Languages Supported: en, es, pt
- Logo Upload: (select file)
- Favicon Upload: (select file)
- Contact Info:
  - Support Email: support@super777.com
  - Support Phone: +1-555-0123
- Timezone: UTC+1
- Country Availability: ES, PT, BR

3. "Create" button
```### Para Birimi Yönetimi

Para birimleri ve döviz kurları.

**Görüntülenen Bilgiler:**
- Para Birimi Kodu (USD, EUR, TRY, GBP)
- Sembol ($, €, ₺, £)
- Döviz Kuru (Baz: USD = 1.0)
- Min/Max Para Yatırma
- Min/Max Bahis

**Döviz Kurlarını Güncelleme:**```
1. Currencies tab
2. "Sync Rates" button
3. Current rates pulled from external API
4. Automatic update
```### Ülke Kuralları

Ülke bazlı kısıtlamalar ve kurallar.

**Sütunlar:**
- Ülke Adı & Kodu
- İzinli (Evet/Hayır)
- İzin Verilen Oyunlar
- İzin Verilen Bonuslar
- KYC Seviyesi (1, 2, 3)
- Ödeme Kısıtlamaları

### Platform Varsayılanları

Global sistem varsayılanları.

**Ayarlar:**```
- Default Language: en
- Default Currency: USD
- Default Timezone: UTC
- Session Timeout: 30 minutes
- Password Min Length: 8 characters
- Require 2FA: No (optional)
- Cache TTL: 300 seconds
- Pagination: 20 items per page
- API Rate Limit: 60 requests/minute
```### API Anahtarı Yönetimi

API anahtarları ve webhook yönetimi.

**API Anahtarı Oluşturma:**```
1. API Keys tab
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
API Key: sk_live_***REDACTED*** (SHOWN ONCE)
Key ID: key_789

⚠️ Save the API key in a secure location!
```---

## En İyi Uygulamalar

### Güvenlik
1. ✅ Tüm yöneticiler için 2FA’yı etkinleştirin
2. ✅ IP beyaz listesini kullanın
3. ✅ API anahtarlarını düzenli olarak değiştirin
4. ✅ Loglarda hassas verileri maskeleyin
5. ✅ Düzenli güvenlik denetimleri yapın

### Operasyonel
1. ✅ Günlük raporları gözden geçirin
2. ✅ Para çekme kuyruğunu günde 2-3 kez kontrol edin
3. ✅ Risk vakalarını 24 saat içinde çözün
4. ✅ Oyuncu şikayetlerine hızlı yanıt verin
5. ✅ Düzenli yedekleme alın

### Test
1. ✅ Simülasyon Laboratuvarı’nda yeni oyunları test edin
2. ✅ RTP değişikliklerini simüle edin
3. ✅ Feature flag’leri %10’dan başlatın
4. ✅ A/B testlerinde minimum 5K örneklem büyüklüğü
5. ✅ Bonus ROI’sini sürekli izleyin

### Uyumluluk
1. ✅ KYC doğrulamalarını güncel tutun
2. ✅ AML eşiklerini düzenli olarak gözden geçirin
3. ✅ Lisans gerekliliklerine uyun
4. ✅ Oyunculara RG araçlarını tanıtın
5. ✅ Denetim loglarını saklayın

---

## Klavye Kısayolları

- `Ctrl+K` - Global arama
- `Ctrl+/` - Komut paleti
- `Ctrl+R` - Verileri yenile
- `Ctrl+E` - Mevcut görünümü dışa aktar
- `Esc` - Modal/diyaloğu kapat

---

## Sürüm Bilgileri

**Sürüm:** 2.0.0  
**Son Güncelleme:** Aralık 2024  
**Platform:** FastAPI + React + MongoDB

---

**💡 İpucu:** Bu kılavuz düzenli olarak güncellenir. En güncel sürüm için `/docs` yolunu kontrol edin.