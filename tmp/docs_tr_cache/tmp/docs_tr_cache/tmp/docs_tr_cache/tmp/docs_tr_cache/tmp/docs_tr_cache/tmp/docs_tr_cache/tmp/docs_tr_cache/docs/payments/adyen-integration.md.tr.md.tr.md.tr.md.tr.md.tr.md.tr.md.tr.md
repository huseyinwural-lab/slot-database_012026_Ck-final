# Adyen Ödeme Entegrasyonu

## Genel Bakış
Bu entegrasyon, oyuncuların Adyen Payment Links kullanarak para yatırmasına olanak tanır. Gerçek Adyen kimlik bilgileri olmadan geliştirme ve test için bir mock modu destekler.

## Mimari

### Backend
- **Servis**: `app.services.adyen_psp.AdyenPSP`
  - `create_payment_link` ve `verify_webhook_signature` işlemlerini yönetir.
  - `dev` modunda `allow_test_payment_methods=True` iken, başarı sayfasına hemen yönlendiren bir mock URL döndürür.
- **Rotalar**: `app.routes.adyen_payments`
  - `POST /checkout/session`: Beklemede bir işlem ve bir Adyen Payment Link oluşturur.
  - `POST /webhook`: İşlemleri tamamlamak için Adyen'den gelen `AUTHORISATION` olaylarını işler.
  - `POST /test-trigger-webhook`: CI/CD E2E testi için simülasyon endpoint'i.
- **Yapılandırma**:
  - `adyen_api_key`: API Anahtarı (`dev` ortamında isteğe bağlı).
  - `adyen_merchant_account`: Merchant Account Kodu.
  - `adyen_hmac_key`: Webhook HMAC Anahtarı.

### Frontend
- **Sayfa**: `WalletPage.jsx`
- **Akış**:
  1. Kullanıcı "Adyen" seçer ve tutarı girer.
  2. Frontend `/checkout/session` çağrısı yapar.
  3. Backend `{ url: "..." }` döndürür.
  4. Frontend kullanıcıyı Adyen'e (veya mock URL'ye) yönlendirir.
  5. Adyen kullanıcıyı `/wallet?provider=adyen&resultCode=Authorised` adresine geri yönlendirir.
  6. Frontend `resultCode` değerini algılar ve başarı mesajı gösterir.

## Test

### E2E Testi
- `e2e/tests/adyen-deposit.spec.ts`
- Tüm akışı doğrular: Kayıt -> Para Yatırma -> Mock Yönlendirme -> Webhook Simülasyonu -> Bakiye Güncellemesi.

### Simülasyon
Başarılı bir ödemeyi manuel olarak simüle edebilirsiniz:```bash
curl -X POST http://localhost:8001/api/v1/payments/adyen/test-trigger-webhook \
  -H "Content-Type: application/json" \
  -d '{"tx_id": "YOUR_TX_ID", "success": true}'
```## Prodüksiyon Kurulumu
1. Ortam değişkenlerinde `ADYEN_API_KEY`, `ADYEN_MERCHANT_ACCOUNT`, `ADYEN_HMAC_KEY` değerlerini ayarlayın.
2. `ALLOW_TEST_PAYMENT_METHODS=False` olduğundan emin olun.
3. Adyen Customer Area'yı webhooks'ları `https://your-domain.com/api/v1/payments/adyen/webhook` adresine gönderecek şekilde yapılandırın.