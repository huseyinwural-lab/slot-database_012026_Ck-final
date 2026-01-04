# Casino Admin Platform - Backend

## 🛠 Kurulum & Yükleme

### Ön Koşullar
- Python 3.11+
- PostgreSQL 15+ (veya Docker ile postgres servisi)
- Supervisor (isteğe bağlı, production için)

### Yükleme

1.  **Depoyu klonlayın**
2.  **Sanal ortam oluşturun:**```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```3.  **Bağımlılıkları yükleyin:**```bash
    pip install -r requirements.txt
    ```4.  **Ortam Değişkenleri:**
    `.env.example` dosyasını `.env` olarak kopyalayın ve değerleri güncelleyin.```bash
    cp .env.example .env
    ```## 🚀 Sunucuyu Çalıştırma

### Geliştirme (Hot Reload)```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```### Production (Supervisor)
Supervisor’ın uvicorn sürecini çalıştıracak şekilde yapılandırıldığından emin olun.

## 📦 Veritabanı Tohumlama

Platformun çalışması için başlangıç verileri (Tenants, Roles, Games) gereklidir.

**1. Varsayılan Tohumlama (Tenants & Roles):**
Başlangıçta otomatik olarak çalışır.

**2. Tam Demo Verisi (Games, Players, Transactions):**```bash
python -m scripts.seed_complete_data
```## 🧪 Test

Birim ve entegrasyon testlerini çalıştırın:```bash
pytest
```## 🔑 Temel Özellikler
- **Çoklu Kiracılık:** Tek kod tabanı, birden fazla izole kiracı.
- **RBAC:** Platform Sahibi vs Kiracı Yöneticisi (Finans, Operasyonlar, Destek).
- **Güvenlik:** Kiracı izolasyonu ara katmanı (middleware), RBAC korumaları.