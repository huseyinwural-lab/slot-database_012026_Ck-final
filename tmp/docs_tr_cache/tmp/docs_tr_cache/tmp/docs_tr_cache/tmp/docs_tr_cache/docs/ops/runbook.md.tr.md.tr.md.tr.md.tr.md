# Nöbet Runbook'u

## Roller
- **Seviye 1 (Ops):** Dashboard'u izleyin, $1000'ın altındaki iadeleri yönetin.
- **Seviye 2 (Dev):** Webhook hataları, 1 saatten uzun süredir takılı kalan ödeme.

## Rutin Kontroller
1. **Günlük:** Kırmızı bayraklar için `/api/v1/ops/dashboard` kontrol edin.
2. **Günlük:** `ReconciliationRun` durumunun "success" olduğunu doğrulayın.

## Olay Müdahalesi
### "Ödeme Takıldı"
1. `status='payout_pending'` ve `updated_at < NOW() - 1 hour` olan `Transaction` kayıtlarını sorgulayın.
2. Hatalar için `PayoutAttempt` kontrol edin.
3. `provider_ref` varsa, Adyen/Stripe Dashboard'unda durumu kontrol edin.
4. Adyen "Paid" diyorsa, TX'i manuel olarak `completed` durumuna güncelleyin.

### "Para Yatırma Eksik"
1. Kullanıcıdan `session_id` veya tarih isteyin.
2. Bu ID için loglarda arama yapın.
3. Loglarda bulunup DB'de yoksa, `Reconciliation` çalıştırın.