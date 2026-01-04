# Gerçek PSP Entegrasyon Kılavuzu (Stripe)

## Ortam Yapılandırması
Aşağıdaki değişkenlerin `backend/.env` dosyasında ayarlandığından emin olun:```bash
STRIPE_API_KEY=sk_test_...  # Secret Key from Stripe Dashboard (Test Mode)
```Frontend için, oturum oluşturma konusunda backend’e dayandığı için herhangi bir özel env değişkenine ihtiyaç yoktur.

## Webhook Kurulumu
Uygulama şu adreste bir webhook endpoint’i sunar:
`POST /api/v1/payments/stripe/webhook`

### Yerel Geliştirme
Webhook’ları yerelde test etmek için, event’leri yönlendirmek üzere Stripe CLI’yi kullanın:```bash
stripe listen --forward-to localhost:8001/api/v1/payments/stripe/webhook
```Veya sağlanan test betiğini `test_stripe.sh` (varsa) ya da E2E simülasyon endpoint’ini kullanın.

## Yerel Test Akışı
1.  **Ödemeyi Başlatın**:
    -   Cüzdan Sayfasına gidin.
    -   "Deposit" seçin, tutarı girin, "Pay with Stripe"e tıklayın.
2.  **Yönlendirme**:
    -   Stripe’ın barındırılan checkout sayfasına yönlendirileceksiniz.
3.  **Ödemeyi Tamamlayın**:
    -   Stripe test kart numaralarını kullanın (örn. `4242 4242 4242 4242`).
4.  **Geri Dönüş**:
    -   Cüzdan sayfasına geri yönlendirilirsiniz.
    -   Uygulama durum güncellemeleri için sorgulama (polling) yapar.
    -   Başarılı olduğunda bakiye otomatik olarak güncellenir.

## Hata Modları
-   **İmza Doğrulaması Başarısız**: `STRIPE_API_KEY` değerini kontrol edin ve webhook secret’ının (kullanılıyorsa) eşleştiğinden emin olun.
-   **İdempotency Çakışması**: Aynı oturum kimliği yeniden işlendiğinde, sistem `Transaction` durum kontrolleri aracılığıyla bunu sorunsuz şekilde ele alır.
-   **Ağ Hatası**: Frontend polling, zaman aşımına uğramadan önce 20 saniye boyunca yeniden dener.

## E2E Testi
CI/CD için, otomatik testler sırasında gerçek Stripe API’lerini çağırmamak adına bir simülasyon endpoint’i kullanıyoruz:
`POST /api/v1/payments/stripe/test-trigger-webhook`
Bu endpoint **prodüksiyonda devre dışıdır**.