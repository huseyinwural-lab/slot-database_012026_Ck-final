# Sprint A: Çekirdek Sertleştirme ve Otomasyon - Görev Sırası

**Durum:** AKTİF
**Hedef:** Finansal hijyeni otomatikleştirmek, güvenlik açıklarını kapatmak ve uyumluluk operasyonlarını etkinleştirmek.

---

## 1. P0-08: Velocity Engine (Oran Sınırlama Mantığı)
**Amaç:** İşlem spam’ini önlemek (örn. dakikada 50 çekim talebi).

*   **Görev 1.1:** `config.py` içine `MAX_TX_VELOCITY` ekle.
*   **Görev 1.2:** `tenant_policy_enforcement.py` içinde `check_velocity_limit` uygula.
    *   Sorgu: Son `window` dakika içinde kullanıcı için işlemleri say.
*   **Görev 1.3:** `player_wallet.py` içine entegre et (Yatırma/Çekme rotaları).

## 2. P0-03: Çekim Süre Dolumu Otomasyonu
**Amaç:** "Requested" durumunda sonsuza dek kilitli kalan fonları serbest bırakmak.

*   **Görev 2.1:** `scripts/process_withdraw_expiry.py` oluştur.
    *   24 saatten eski `requested` işlemlerini bul.
    *   Döngü:
        *   İade için Ledger çağır (Held->Avail).
        *   İşlem Durumu -> `expired` olarak güncelle.
        *   Denetim kaydı (Audit) logla.

## 3. P0-07: Chargeback İşleyicisi
**Amaç:** "Forced Refund" olaylarını güvenli şekilde ele almak.

*   **Görev 3.1:** `POST /api/v1/finance/chargeback` endpoint’ini oluştur/güncelle.
*   **Görev 3.2:** Ledger Mantığını uygula (Zorunlu Borçlandırma).
    *   Negatif bakiyeye izin ver.
    *   İşlem Durumu -> `chargeback` olarak güncelle.

## 4. P0-13/14: Uyumluluk UI
**Amaç:** Backend mantığını Frontend butonlarına bağlamak.

*   **Görev 4.1:** Admin UI - KYC Onay Butonu.
*   **Görev 4.2:** Oyuncu UI - Kendi Kendini Dışlama Butonu.

---

**Uygulama Başlangıcı:** Hemen.
**Sahip:** E1 Agent.