# Sprint C: Kontrollü Casino - Görev Sırası

**Durum:** AKTİF  
**Hedef:** Rastgele mock mantığını deterministik Math Engine (Robot Registry) ile değiştirmek.

---

## 1. C1 & C2: Robot Registry & Math Varlıkları
*   **Görev 1.1:** `app/models/robot_models.py` oluşturun.
    *   `RobotDefinition`, `MathAsset`, `GameRobotBinding`.
*   **Görev 1.2:** Alembic Migration.
*   **Görev 1.3:** Seed Script `scripts/seed_robots.py`.
    *   "Basic Slot Robot" ve onun Reelset/Paytable verilerini ekleyin.

## 2. C3: Akıllı Oyun Motoru
*   **Görev 2.1:** `app/services/slot_math.py` oluşturun.
    *   Reelset’i ayrıştırma, sembolleri seçme, paylines kontrol etme mantığı.
*   **Görev 2.2:** `app/routes/mock_provider.py` dosyasını güncelleyin.
    *   `Math.random()` yerine `slot_math` kullanın.

## 3. C5: Admin UI
*   **Görev 3.1:** Backend Router `app/routes/robots.py`.
*   **Görev 3.2:** Frontend `RobotsPage.jsx`.

---

**Çalıştırma Başlangıcı:** Derhal.