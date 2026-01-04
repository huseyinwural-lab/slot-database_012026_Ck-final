# Poker Sağlayıcı Sözleşmesi v1 (Cash)

**Sürüm:** 1.0
**Tarih:** 2025-12-26

## 1. Genel Bakış
Poker Oyunu entegrasyonu için standartlaştırılmış arayüz. "Seamless Wallet" üzerinden Cash Oyunlarını destekler.

## 2. Güvenlik
- **Kimlik Doğrulama:** HMAC-SHA256 İmzası + Zaman Damgası.
- **İdempotensi:** Tüm finansal olaylar için zorunlu `transaction_id` (Sağlayıcı TX ID).
- **Başlıklar:** `X-Signature`, `X-Timestamp`.

## 3. Uç Noktalar

### 3.1 Kimlik Doğrulama
**POST** `/api/v1/integrations/poker/auth`
- **Girdi:** `token`
- **Çıktı:** `player_id`, `currency`, `balance`

### 3.2 İşlem (Borçlandırma/Alacaklandırma)
**POST** `/api/v1/integrations/poker/transaction`
- **Yük:**
  - `type`: `DEBIT` | `CREDIT` | `ROLLBACK`
  - `amount`: float
  - `round_id`: string (El ID)
  - `transaction_id`: string (Benzersiz Sağlayıcı TX ID)
- **Yanıt:**
  - `status`: `OK`
  - `balance`: float
  - `ref`: string

### 3.3 Denetim (El Geçmişi)
**POST** `/api/v1/integrations/poker/hand-history`
- **Yük:**
  - `hand_id`: string
  - `table_id`: string
  - `game_type`: `CASH`
  - `pot_total`: float
  - `rake_collected`: float
  - `winners`: list
- **Yanıt:** `OK`

## 4. Hata Kodları
- `INVALID_SIGNATURE` (401)
- `INSUFFICIENT_FUNDS` (402)
- `DUPLICATE_REQUEST` (409) - *İdempotent tekrar oynatma, mevcut verilerle Başarılı 200 olarak ele alınır*
- `INTERNAL_ERROR` (500)