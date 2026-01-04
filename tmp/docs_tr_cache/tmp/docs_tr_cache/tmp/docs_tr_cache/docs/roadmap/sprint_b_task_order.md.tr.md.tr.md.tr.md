# Sprint B: Oyun Entegrasyonu ve Büyüme - Görev Sırası

**Durum:** AKTİF
**Hedef:** Defter (Ledger) bütünlüğü ve temel Bonus/Risk kontrolleri ile çalışan bir Oyun Döngüsü (Bahis/Kazanç) oluşturmak.

---

## 1. B0: Oyun Sağlayıcı Sözleşmesi (Kanonik Model)
*   **Görev 1.1:** `app/models/game_models.py` içinde SQL Modellerini (`Game`, `GameSession`, `GameRound`, `GameEvent`) tanımlayın.
*   **Görev 1.2:** `app/schemas/game_schemas.py` içinde Kanonik Webhook (Bahis/Kazanç/Geri Alma) için Pydantic Şemalarını tanımlayın.

## 2. B1: Oyun Döngüsü -> Cüzdan/Defter (Motor)
*   **Görev 2.1:** `GameEngine` servisini uygulayın.
    *   İdempotensi yönetin (Olay ID kontrolü).
    *   Kilitlemeyi yönetin (Oyuncu Cüzdanı kilidi).
    *   Olay -> Defter Delta eşlemesi (Bahis = Borç, Kazanç = Alacak).
*   **Görev 2.2:** `Integrations` Router’ını uygulayın (`/api/v1/integrations/callback`).

## 3. B5: Sahte Sağlayıcı (Simülasyon)
*   **Görev 3.1:** `MockProvider` Router’ını oluşturun (`/api/v1/mock-provider`).
    *   `launch`, `spin` simülasyonu için endpoint’ler (B1’e callback tetikler).

## 4. B2: Katalog ve Frontend
*   **Görev 4.1:** Oyun Listesi ve Launch URL’i için API.
*   **Görev 4.2:** Frontend Oyuncu - Oyun Kataloğu Sayfası.
*   **Görev 4.3:** Frontend Oyuncu - Oyun Penceresi (Iframe).

## 5. B3: Bonus MVP (Hafif)
*   **Görev 5.1:** `Player` modelini `wagering_remaining` ile güncelleyin.
*   **Görev 5.2:** Uygunsa Bonus bakiyesinden düşecek şekilde `GameEngine`’i güncelleyin.

---

**Yürütme Başlangıcı:** Hemen.