# Sprint B Final: Güvenlik & E2E - Görev Sırası

**Durum:** AKTİF  
**Hedef:** Oyun Döngüsünü sağlamlaştırmak (HMAC, Replay, İdempotensi) ve katı E2E ile doğrulamak.

---

## 1. B-FIN-01: Callback Güvenliği (HMAC + Nonce)
*   **Görev 1.1:** `app/middleware/callback_security.py` içindeki `CallbackSecurityMiddleware` güncelle.
    *   Nonce Replay kontrolü ekle (`CallbackNonce` tablosunu kullanarak).
    *   Katı HMAC hesaplamasını zorunlu kıl (Ham Body).
*   **Görev 1.2:** `app/models/game_models.py` içinde `CallbackNonce` Modeli oluştur.
*   **Görev 1.3:** Modeli Alembic’e kaydet ve migrate et.

## 2. B-FIN-02: İdempotensi (Event Seviyesi)
*   **Görev 2.1:** `GameEvent` kısıtlarını doğrula (zaten `unique=True`).
*   **Görev 2.2:** `GameEngine`’in `IntegrityError`’ı zarif şekilde ele aldığından emin ol (200 OK + Bakiye döndür).

## 3. B-FIN-03: Mock Provider İmzalama
*   **Görev 3.1:** `mock_provider.py` dosyasını güncelle.
    *   `X-Callback-Timestamp`, `X-Callback-Nonce`, `X-Callback-Signature` oluştur.
    *   İmzalama için `adyen_hmac_key` (veya sağlayıcıya özel secret) kullan.

## 4. B-FIN-04: E2E Testi
*   **Görev 4.1:** İmza doğrulama kontrollerini (Happy Path) dahil edecek şekilde `game-loop.spec.ts` dosyasını güncelle.
*   **Görev 4.2:** Negatif yollar (403, 409) için `backend/tests/test_callback_security.py` oluştur.

---

**Uygulama Başlangıcı:** Hemen.