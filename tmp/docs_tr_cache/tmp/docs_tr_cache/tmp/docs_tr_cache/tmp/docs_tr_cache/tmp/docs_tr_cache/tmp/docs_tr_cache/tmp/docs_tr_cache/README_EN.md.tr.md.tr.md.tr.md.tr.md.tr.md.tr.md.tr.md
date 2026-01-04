# Casino Platformu - Kullanıcı Kılavuzu

Bu proje, yüksek düzeyde regüle edilen, denetlenebilir ve ölçeklenebilir bir **Casino ve Bahis Platformu**dur.
Finansal defter, risk yönetimi, çok oyunculu poker motoru, bonus motoru ve modern bir yönetim paneli içerir.

---

## 🏗️ Mimari Genel Bakış

*   **Backend:** Python (FastAPI), AsyncIO, SQLModel (ORM).
*   **Veritabanı:** PostgreSQL (Prod), SQLite (Dev). Tüm şema değişiklikleri **Alembic** üzerinden yönetilir.
*   **Frontend:** React, Tailwind CSS, Shadcn UI.
*   **Operasyonlar:** Supervisor tarafından yönetilen servisler, Docker ile uyumlu yapı.

### Temel Modüller
1.  **Çekirdek Finans (Defter):** Çift kayıtlı muhasebe sistemi. Her işlem (Deposit, Bet, Win, Withdraw) `ledgertransaction` tablosunda bir hash zinciri ile saklanır.
2.  **Poker Motoru:** Multi-Table Tournament (MTT) ve Cash Game desteği.
3.  **Risk ve Uyumluluk:** KYC (Know Your Customer), RG (Responsible Gaming) ve Collusion tespiti.
4.  **Büyüme:** Affiliate sistemi, A/B testleri ve Smart Offer motoru.

---

## 🚀 Kurulum ve Çalıştırma

### Ön Koşullar
*   Python 3.11+
*   Node.js 18+ (Yarn)
*   PostgreSQL (Opsiyonel, yerel geliştirme için varsayılan SQLite)

### Kurulum Adımları

> **Not (Prod/Staging / CI_STRICT):**
> - `ENV=prod|staging` veya `CI_STRICT=1` olduğunda `DATABASE_URL` **zorunludur** ve **sqlite URL'leri yasaktır**.
> - `SYNC_DATABASE_URL` kanonik addır. Eski `DATABASE_URL_SYNC` yalnızca geriye dönük uyumluluk için tutulur.

1.  **Backend Kurulumu:**```bash
    cd backend
    pip install -r requirements.txt
    ```2.  **Frontend Kurulumu:**```bash
    cd frontend
    yarn install
    ```3.  **Veritabanı Hazırlığı (Migrasyon):**```bash
    cd backend
    alembic upgrade head
    ```4.  **Servisleri Başlatma (Supervisor üzerinden):**
    Proje kök dizininde:```bash
    sudo supervisorctl start all
    ```Veya manuel olarak:
    *   Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8001`
    *   Frontend: `yarn start` (Port 3000)

---

## 🧪 Test ve Doğrulama

Sistem katı "Release Gates" ile korunur. Canlıya çıkmadan önce aşağıdaki testler çalıştırılmalıdır:

### 1. E2E Smoke Test (Release Matrix)
Tüm kritik iş akışlarını (Payments, Poker, Bonus, Risk) tek seferde test eder:```bash
python3 /app/scripts/release_smoke.py
```### 2. Migrasyon Kontrolü
Veritabanı şemasının kod ile eşleştiğini doğrular:```bash
python3 /app/scripts/ci_schema_guard.py
```### 3. Dağıtım Ön Kontrolleri
Canlıya çıkmadan önceki son kontroller (Ortam değişkenleri, DB bağlantısı):```bash
python3 /app/scripts/deploy_preflight.py
```---

## 🛠️ Operasyonel Kılavuzlar (Runbook'lar)

Kritik durumlar için ayrıntılı prosedürler `/app/artifacts/production_readiness/runbooks/` altında bulunabilir:

*   **Olay Müdahalesi:** Sistem kesintileri veya saldırılar sırasında izlenecek adımlar.
*   **Geri Alma Prosedürü:** Hatalı bir dağıtımın nasıl geri alınacağı.
*   **Mutabakat Playbook'u:** Ödeme sağlayıcıları ile defter arasındaki tutarsızlıkların nasıl giderileceği.

### Gözlemlenebilirlik
Sistem yapılandırılmış loglar üretir.
*   **Hata Logları:** `/var/log/supervisor/backend.err.log`
*   **Erişim Logları:** `/var/log/supervisor/backend.out.log`
*   **Uyarı:** `AlertEngine` script'i, ödeme başarı oranlarını ve risk sinyallerini izlemek için periyodik olarak çalışır.

---

## 🔒 Güvenlik

*   **Değiştirilemez Defter:** Finansal kayıtlar asla silinemez veya güncellenemez. Yalnızca ters kayıtlar (reversal) girilebilir.
*   **RBAC:** Admin rolleri (Owner, Tenant Admin, Support) kesin biçimde ayrılmıştır.
*   **Denetim Kaydı:** Tüm admin aksiyonları `auditevent` tablosunda kaydedilir.

---

**Sürüm:** 1.0.0 (Üretime Hazır)
**İletişim:** Ops Ekibi