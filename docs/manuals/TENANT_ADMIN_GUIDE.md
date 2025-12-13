# 🏢 Kiracı (Casino İşletmecisi) Kullanım Kılavuzu

Bu belge, bir Casino sitesini yöneten **Tenant Admin** ve ekibi (Finans, Operasyon, Destek) içindir.

---

## 1. Giriş
*   **URL:** `http://localhost:3000` (Platform sahibi tarafından size verilen URL)
*   **Giriş:** Size tanımlanan e-posta ve şifre ile giriş yapın.
*   **Panel:** Giriş yaptığınızda panel rengi ve başlığı markanıza özel (Yeşil/Teal tema) açılacaktır.

---

## 2. Personel Yönetimi (Admin Users)
Kendi ekibinizi oluşturun ve yetkilendirin.

1.  Sol menüden **"Admin Users"** sayfasına gidin.
2.  **"Add Admin"** butonuna tıklayın.
3.  Personel bilgilerini girin ve **Rol** seçin:
    *   **Full Admin:** Sizinle aynı yetkilere sahip.
    *   **Finance:** Sadece ödemeleri ve ciroyu görür.
    *   **Operations:** Sadece oyuncuları ve oyunları görür.
    *   **Support:** Sadece oyuncu detaylarını görür (düzenleyemez).
4.  Personel, davet linki veya belirlediğiniz şifre ile sisteme girebilir.

---

## 3. Finans ve Ödeme Onayları
Oyuncularınızın para çekme taleplerini yönetin.

1.  Sol menüden **"Finance"** sayfasına gidin.
2.  Tabloda **"Pending"** (Bekleyen) statüsündeki işlemleri bulun.
3.  İşleme tıklayarak detayları açın:
    *   **Risk Analizi:** Sağ tarafta AI risk skorunu kontrol edin.
    *   **Ödeme Kanalı:** "Payout Method" kutusundan ödemeyi nasıl yaptığınızı seçin (Papara, Havale, Kripto vb.).
    *   **Onay:** **"Approve Payout"** butonuna basarak işlemi tamamlayın. Oyuncu bakiyesi düşecek ve işlem tamamlanacaktır.

---

## 4. Oyun Yönetimi (Games)
Sitenizdeki oyunları yönetin.

1.  Sol menüden **"Games"** sayfasına gidin.
2.  Aktif/Pasif durumunu değiştirmek istediğiniz oyunu seçin.
3.  **RTP Ayarı (Varsa):** Eğer paketinizde "Config Edit" özelliği varsa, oyunun detayına girip **"Game Config"** sekmesinden RTP (Kazanma Oranı) ayarlarını değiştirebilirsiniz.

---

## 5. Ciro Takibi (My Revenue)
1.  Sol menüden **"My Revenue"** sayfasına gidin.
2.  Tarih aralığı seçerek **GGR (Gross Gaming Revenue)**, Toplam Bahis, Toplam Kazanç ve Kar/Zarar durumunuzu anlık izleyin.
