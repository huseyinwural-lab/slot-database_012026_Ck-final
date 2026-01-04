# Webhook Hata Giderme Kılavuzu

## 1. İmza Doğrulama Hatası
**Belirti:** `/api/v1/payments/*/webhook` için `401 Unauthorized` yanıtları.
**Uyarı:** `Log error: "Webhook Signature Verification Failed"`
**Eylem:**
1. Ortam değişkenlerinde `ADYEN_HMAC_KEY` veya `STRIPE_WEBHOOK_SECRET` değerlerini kontrol edin.
2. Sağlayıcının (Adyen/Stripe) anahtarları döndürüp döndürmediğini doğrulayın.
3. Sorun devam ederse, hata ayıklamak için ham header loglamayı geçici olarak etkinleştirin (PII konusunda dikkatli olun).

## 2. Replay Fırtınası
**Belirti:** Aynı `provider_event_id` için birden fazla webhook.
**Uyarı:** `Log info: "Replay detected"` sayısı > 100/dk.
**Eylem:**
1. Bu genellikle zararsızdır (Idempotency bunu yönetir).
2. Yük yüksekse IP’yi engelleyin veya sağlayıcıyla iletişime geçin.

## 3. Rate Limit
**Belirti:** Sağlayıcıyı çağırdığımızda (örn. Payout sırasında) sağlayıcı 429 döner.
**Uyarı:** Loglarda `HTTP 429`.
**Eylem:**
1. Takılı kalan öğeler için `PayoutAttempt` tablosunu kontrol edin.
2. Backoff sonrası manuel olarak yeniden deneyin.