# Poker Entegrasyon Spesifikasyonu

**Sürüm:** 1.0  
**Tarih:** 2025-12-26

## 1. Genel Bakış
Entegrasyon, Sağlayıcı’nın Oyun Motoru olarak, platformumuzun ise Cüzdan/Defter (Wallet/Ledger) olarak hareket ettiği bir "Sorunsuz Cüzdan" (Seamless Wallet) modelini izler.

## 2. API Uç Noktaları

### 2.1 Başlatma Kimlik Doğrulaması
**POST** `/api/v1/integrations/poker/auth`
- **Girdi:** `token`
- **Çıktı:** `player_id`, `currency`, `balance`

### 2.2 İşlem (Borç/Alacak)
**POST** `/api/v1/integrations/poker/transaction`
- **Yük (Payload):**
  - `type`: `DEBIT` (Buy-in/Bahis) veya `CREDIT` (Kazanç/Nakit Çekim)
  - `amount`: float
  - `round_id`: string (El ID)
  - `transaction_id`: string (Benzersiz Sağlayıcı TX ID)
- **Yanıt:**
  - `status`: `OK`
  - `balance`: float (Yeni Bakiye)
  - `ref`: string (Platform TX ID)

### 2.3 El Geçmişi (Denetim)
**POST** `/api/v1/integrations/poker/hand-history`
- **Yük (Payload):**
  - `hand_id`: string
  - `pot_total`: float
  - `rake_collected`: float
  - `winners`: list
- **Yanıt:** `OK`

## 3. Rake ve Ekonomi
- **Rake Hesaplaması:** Dahili olarak doğrulanır. %1'den büyük tutarsızlıklar uyarıları tetikler.
- **Rakeback:** `rake_collected` baz alınarak günlük hesaplanır.

## 4. Güvenlik
- **İdempotency:** `transaction_id` üzerinde zorunludur.
- **İmza:** Header'larda HMAC-SHA256 zorunludur.