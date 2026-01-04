# Sprint B (Bölüm 2): Frontend & Güvenlik - Görev Sırası

**Durum:** AKTİF  
**Hedef:** Görünür Casinoyu (Katalog, Pencere) oluşturmak ve görünmez Motoru güvence altına almak.

---

## 1. P0-Frontend: Katalog & Pencere
*   **Görev 1.1:** `GameCatalog.jsx` oluşturun (Liste & Arama).
    *   API: `GET /api/v1/games`.
*   **Görev 1.2:** `GameRoom.jsx` oluşturun (Oyun Penceresi).
    *   API: `POST /api/v1/games/launch`.
    *   Bileşen: `MockGameFrame` (iframe/oyun istemcisini simüle eder).
    *   Mantık: `mock-provider/spin` çağırır -> Bakiyeyi günceller.

## 2. P0-Güvenlik: Callback Geçidi
*   **Görev 2.1:** `CallbackSecurityMiddleware` uygulayın (veya bağımlılık).
    *   `X-Signature` (HMAC) kontrol edin.
    *   `X-Timestamp` (Replay) kontrol edin.
    *   IP doğrulayın (Allowlist).

## 3. P0-E2E: Tam Simülasyon
*   **Görev 3.1:** `e2e/tests/game-loop.spec.ts` yazın.
    *   Giriş -> Kataloğu Aç -> Oyunu Başlat -> Spin -> Bakiyeyi Doğrula.

---

**Yürütme Başlangıcı:** Hemen.