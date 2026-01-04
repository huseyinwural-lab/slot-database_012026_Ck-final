# Sprint C - Görev 2: Akıllı Oyun Motoru - Görev Sırası

**Durum:** AKTİF  
**Hedef:** Kayıtlı varlıkları kullanarak oyun sonuçlarını belirleyen deterministik "Math Engine"i uygulamak.

---

## 1. C2.1: Spin İstek Akışı
*   **Görev 1.1:** `mock_provider.py` dosyasını güncelle (Spin Endpoint).
    *   `game_id` kabul et (veya oturumdan çıkar).
    *   `SlotMath.calculate_spin` çağır.
    *   `GameEngine.process_event` çağır (Bet/Win).
    *   Kapsamlı yanıt döndür (Grid, Wins, Audit).

## 2. C2.2: DB Çözümleme Mantığı
*   **Görev 2.1:** `app/services/slot_math.py` oluştur.
    *   `load_robot_context(session_id)`: Binding -> Robot -> Config -> MathAssets verilerini getirir.
    *   Aktif durumunu doğrular.

## 3. C2.3 - C2.5: Deterministik RNG ve Mantık
*   **Görev 3.1:** `generate_grid(reelset, seed)` uygula.
*   **Görev 3.2:** `calculate_payout(grid, paytable)` uygula.
    *   Orta çizgi mantığını destekle.

## 4. C2.7: Denetim
*   **Görev 4.1:** Ayrıntılı matematik kökenini (hash'ler, seed'ler, grid) depolamak için `GameEvent`i güncelle veya `GameRoundAudit` modeli oluştur.

---

**Yürütmeye Başlama:** Derhal.  
**Sahip:** E1 Agent.