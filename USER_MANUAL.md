# 🎰 Casino Admin Panel - Kullanım Kılavuzu (Python/React)

Bu proje, **FastAPI (Backend)**, **React (Frontend)** ve **MongoDB** teknolojileri kullanılarak geliştirilmiş modern, ölçeklenebilir ve güvenli bir Casino Yönetim Paneli'dir.

---

## 🚀 Kurulum ve Başlatma

Bu proje Emergent platformunda otomatik olarak çalışmaktadır. Kendi sunucunuzda çalıştırmak isterseniz:

### Gereksinimler
*   Python 3.11+
*   Node.js 18+
*   MongoDB 6.0+

### Backend Başlatma
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# .env dosyasını düzenleyin (MONGO_URL vb.)
python server.py
# Veya uvicorn ile: uvicorn server:app --reload --port 8001
```

### Frontend Başlatma
```bash
cd frontend
yarn install
yarn start
```

---

## 🔑 API Konfigürasyonu (Önemli)

Gerçek entegrasyonların çalışması için `/app/backend/.env` dosyasına API anahtarlarınızı girmelisiniz:

```env
OPENAI_API_KEY=sk-proj-...   # Fraud analizi için
SENDGRID_API_KEY=SG....      # Email gönderimi için
```

---

## 📱 Modüller ve Kullanım

### 1. Dashboard (Ana Panel)
*   **Özet:** Günlük ciro, aktif oyuncu sayısı, bekleyen çekim talepleri.
*   **Grafikler:** Son 7 günlük gelir trendi.
*   **Son Kayıtlar:** Sisteme yeni katılan son 5 oyuncu.

### 2. Oyuncu Yönetimi (Players)
*   **Liste:** Tüm oyuncuları arayın, bakiyesine veya statüsüne göre filtreleyin.
*   **Detay:** Oyuncunun ismine tıklayarak profile gidin.
    *   **Profile:** Kişisel bilgiler ve bakiye özeti.
    *   **KYC:** Yüklenen belgeleri onaylayın/reddedin.
    *   **Game History:** Oynadığı oyunları ve kazanç/kayıp durumunu görün.
    *   **Logs:** Giriş ve IP logları.
*   **Aksiyonlar:** Sağ üstten oyuncuyu "Suspend" (Dondur) veya "Activate" (Aktif Et) yapabilirsiniz.

### 3. Finans Yönetimi (Finance & Approval)
*   **Finance:** Para yatırma ve çekme taleplerini listeleyin. "Pending" olanları tek tıkla onaylayın.
*   **Approval Queue (4-Eyes):** Yüksek tutarlı işlemler (Örn: >$1000 çekimler) doğrudan onaylanmaz. Bu kuyruğa düşer ve **ikinci bir onaya** ihtiyaç duyar.
    *   `Sidebar -> Approval Queue` menüsünden bu işlemleri inceleyip "Approve" veya "Reject" diyebilirsiniz.

### 4. Oyun Yönetimi (Games)
*   **Listeleme:** Aktif oyunları, RTP oranlarını ve sağlayıcılarını görün.
*   **Ekleme:** "Add Game" butonu ile yeni slot/canlı oyun ekleyin.
*   **Durum:** Switch butonu ile oyunu anında bakıma alabilir (Inactive) veya açabilirsiniz (Active).

### 5. Bonus Yönetimi (Bonuses)
*   **Kampanyalar:** Hoşgeldin bonusu, kayıp bonusu gibi kurgular yaratın.
*   **Kurallar:** Çevrim şartı (Wager Req) ve bonus miktarını belirleyin.

### 6. Risk & Fraud (Risk Yönetimi)
*   **Fraud Check:** Bir işlemi manuel olarak simüle edip OpenAI risk skorunu görün.
    *   *Girdi:* Tutar, IP, Email.
    *   *Çıktı:* Risk Skoru (%), Güven Oranı ve Öneri (Örn: "High Risk - Block User").
*   **Risk Rules:** Otomatik kuralları (Örn: "Aynı IP'den 5 hesap açılırsa blokla") yönetin.

### 7. CRM & Destek
*   **Support:** Kullanıcılardan gelen destek biletlerini (Tickets) yanıtlayın. Canlı sohbet arayüzü mevcuttur.
*   **CRM:** E-posta/SMS kampanyaları oluşturun.

### 8. Sistem Ayarları
*   **Feature Flags:** Yeni özellikleri kod deploy etmeden açıp kapatın. (Örn: "Dark Mode V2" özelliğini %10 kullanıcıya aç).
*   **Logs:** Sistem hatalarını ve kritik işlem loglarını inceleyin.
*   **Admins:** Yeni admin ekleyin ve yetkilendirin.

---

## 🧪 Simülasyon Merkezi (Simulation Lab)

Sistemi canlıya almadan test etmek için geliştirdiğimiz özel laboratuvar.

### Kullanım Adımları:
1.  **Oyuncu Üret:** `Players` sekmesinden 50 adet "High Risk" oyuncu üretin.
2.  **Oyun Oynat:** `Game Engine` sekmesinden bu oyunculara 1000 spin attırın. Kasanın (House Edge) durumunu görün.
3.  **Finans Testi:** `Finance` sekmesinden sahte "Deposit Callback" göndererek bakiyelerin güncellendiğini doğrulayın.
4.  **Zaman Yolculuğu:** `Time Travel` sekmesinden sistemi 3 gün ileri alarak süreli bonusların dolup dolmadığını test edin.

---

## 🆘 Destek

Herhangi bir teknik sorunda `Support -> Tickets` bölümünden teknik ekibe ulaşabilir veya `/app/backend/server.py` içindeki logları inceleyebilirsiniz.

İyi şanslar! 🎰
