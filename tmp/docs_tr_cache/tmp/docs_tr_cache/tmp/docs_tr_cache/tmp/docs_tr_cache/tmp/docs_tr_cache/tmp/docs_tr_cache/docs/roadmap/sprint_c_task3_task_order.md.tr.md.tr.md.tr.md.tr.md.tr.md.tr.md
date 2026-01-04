# Sprint C - Görev 3: Admin UI (Robot Yönetimi) - Görev Sırası

**Durum:** AKTİF
**Hedef:** Math Engine kontrollerini Admin Paneli üzerinden Operasyon ekibine sunmak.

---

## 1. Backend: Robots API
*   **Görev 1.1:** `app/routes/robots.py` oluşturun.
    *   `GET /`: Robotları listele (filtreler).
    *   `POST /{id}/toggle`: Aktifleştir/Devre dışı bırak.
    *   `POST /{id}/clone`: Konfigürasyonu kopyala.
    *   `GET /math-assets`: Varlıkları listele.
*   **Görev 1.2:** `app/routes/games.py` dosyasını güncelleyin (veya yeni route).
    *   `GET /{game_id}/robot`: Bağlamayı al.
    *   `POST /{game_id}/robot`: Bağlamayı ayarla.

## 2. Frontend: Robots Kataloğu
*   **Görev 2.1:** `pages/RobotsPage.jsx` oluşturun.
    *   Tablo: ID, Ad, Konfigürasyon Özeti, Aksiyonlar.
    *   Drawer: Konfigürasyonun JSON görünümü.
*   **Görev 2.2:** `Layout.jsx` sidebar’ına ekleyin (feature gated).

## 3. Frontend: Oyun Bağlama
*   **Görev 3.1:** `pages/GameManagement.jsx` dosyasını güncelleyin (veya Detay).
    *   "Math Engine" sekmesi ekleyin.
    *   Mevcut robotu gösteren kart.
    *   Yeni robot bağlamak için seçici.

## 4. E2E: Admin Ops
*   **Görev 4.1:** `e2e/tests/robot-admin-ops.spec.ts`.
    *   Robotu Kopyala -> Oyuna Bağla -> Spin -> Robot ID’yi Doğrula.

---

**Uygulama Başlangıcı:** Derhal.