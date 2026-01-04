# Sprint B (Bölüm 3): Oyuncu Oyun Deneyimi & Uçtan Uca (E2E) - Görev Sırası

**Durum:** AKTİF  
**Hedef:** Görünür "Casino Döngüsü"nü (Katalog -> Oyna -> Sonuç) teslim etmek ve bunu sıkı E2E testleriyle kanıtlamak.

---

## 1. B2: Oyuncu Frontend & Launch API (P0)
**Hedef:** Oyuncu bir oyun seçebilir ve oynayabilir.

*   **Görev 1.1:** Backend - `GameSession` & Launch Mantığı.
    *   Endpoint: `POST /api/v1/games/launch`.
    *   Mantık: Oyunu Doğrula -> Oturum Oluştur -> Launch URL/Token Döndür.
*   **Görev 1.2:** Frontend - `GameCatalog.jsx`.
    *   UI: Oyun ızgarası, Arama çubuğu.
    *   Entegrasyon: `GET /api/v1/games` çağırır.
*   **Görev 1.3:** Frontend - `GameRoom.jsx` (Mock Pencere).
    *   UI: Iframe konteyneri (simüle), Bakiye göstergesi, Spin butonu.
    *   Entegrasyon: `POST /api/v1/mock-provider/spin` çağırır (istemci tarafı oyun mantığının sağlayıcıyı çağırmasını simüle eder).
*   **Görev 1.4:** Frontend - `GameHistory.jsx`.
    *   UI: Son spin/kazançların listesi.

## 2. B6: Callback Güvenlik Geçidi (P0)
**Hedef:** "Game Engine"i sahte webhook’lara karşı güvenceye almak.

*   **Görev 2.1:** `CallbackSecurityMiddleware` implementasyonu.
    *   `X-Signature` doğrula (HMAC-SHA256).
    *   `X-Timestamp` doğrula (Replay koruması).
    *   `/api/v1/integrations/callback` için uygula.

## 3. B5: E2E Tam Simülasyon (P0)
**Hedef:** Tüm döngüyü uçtan uca doğrulamak.

*   **Görev 3.1:** `e2e/tests/casino-game-loop.spec.ts`.
    *   Akış: Giriş -> Oyun Seç -> Spin -> Cüzdan Güncellemesini Doğrula.
    *   Negatif: Yetersiz bakiye, Geçersiz İmza.

---

**Çalıştırma Başlangıcı:** Hemen.