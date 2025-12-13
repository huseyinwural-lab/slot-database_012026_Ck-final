# 👑 Platform Sahibi Kullanım Kılavuzu

Bu belge, **Süper Admin (Platform Owner)** yetkisine sahip kullanıcılar içindir.

---

## 1. Giriş
*   **URL:** `http://localhost:3000` (veya production domaini)
*   **Varsayılan Hesap:** `admin@casino.com` / `Admin123!`

---

## 2. Kiracı (Tenant) Yönetimi
Sistemin en temel fonksiyonudur. Yeni bir Casino sitesi (B2B Müşteri) oluşturmak için kullanılır.

### Yeni Kiracı Oluşturma
1.  Sol menüden **"Tenants"** (System bölümü altında) sayfasına gidin.
2.  **"Create Tenant"** formunu doldurun:
    *   **Name:** Müşterinin marka adı (Örn: "Galaxy Casino").
    *   **Type:** Genellikle "Renter" seçilir.
    *   **Features:** Müşterinin paketine göre özellikleri açıp kapatın:
        *   `Game Robot`: Simülasyon araçlarını kullanabilsin mi?
        *   `Edit Configs`: Oyun RTP oranlarını değiştirebilsin mi?
        *   `Manage Bonus`: Bonus kampanyası oluşturabilsin mi?
3.  **"Create Tenant"** butonuna basın.

### Kiracı Özelliklerini Düzenleme
1.  Kiracı listesinde ilgili kiracının yanındaki **"Edit Features"** butonuna tıklayın.
2.  İstediğiniz özelliği açıp kapatın ve kaydedin. Değişiklik anında kiracının panelinde aktif olur.

---

## 3. Global Finans & Raporlama
Platformdaki tüm trafiği kuş bakışı görmek için kullanılır.

### Toplam Ciro (All Revenue)
1.  Sol menüden **"All Revenue"** (Core bölümü altında) sayfasına gidin.
2.  Tarih aralığını seçin (Son 24 saat, 7 gün vb.).
3.  Burada tüm kiracıların toplam cirosunu (GGR), toplam bahis ve kazanç miktarlarını görebilirsiniz.

### Finansal İşlemler (Finance)
1.  Sol menüden **"Finance"** sayfasına gidin.
2.  Burada platform genelindeki tüm para yatırma ve çekme işlemleri listelenir.
3.  Şüpheli işlemleri veya büyük çekimleri buradan denetleyebilirsiniz.

---

## 4. Risk & Dolandırıcılık (Fraud)
1.  Sol menüden **"Fraud Check"** sayfasına gidin.
2.  Sistem, AI (Yapay Zeka) destekli olarak riskli işlemleri (aynı IP, çoklu hesap, anormal bahis) otomatik işaretler.
3.  Riskli oyuncuları veya işlemleri buradan engelleyebilirsiniz.
