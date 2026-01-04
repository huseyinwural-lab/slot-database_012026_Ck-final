# Casino Platform - Kullanım Kılavuzu

Bu proje, yüksek regülasyonlu, denetlenebilir ve ölçeklenebilir bir **Casino ve Bahis Platformu**dur. 
Proje; finansal defter (ledger), risk yönetimi, çok oyunculu poker, bonus motoru ve modern bir yönetim paneli içerir.

---

## 🏗️ Mimari Genel Bakış

*   **Backend:** Python (FastAPI), AsyncIO, SQLModel (ORM).
*   **Veritabanı:** PostgreSQL (Prod), SQLite (Dev). Tüm şema değişiklikleri **Alembic** ile yönetilir.
*   **Frontend:** React, Tailwind CSS, Shadcn UI.
*   **Operasyon:** Supervisor ile yönetilen servisler, Docker uyumlu yapı.

### Temel Modüller
1.  **Core Finance (Ledger):** Çift girişli muhasebe sistemi. Her işlem (Deposit, Bet, Win, Withdraw) `ledgertransaction` tablosunda hash zinciri ile saklanır.
2.  **Poker Engine:** Çok masalı turnuva (MTT) ve nakit oyun desteği.
3.  **Risk & Compliance:** KYC (Kimlik Doğrulama), RG (Sorumlu Oyunculuk) ve Collusion (Şike) tespiti.
4.  **Growth:** Affiliate sistemi, A/B testleri ve Akıllı Teklif (Offer) motoru.

---

## 🚀 Kurulum ve Çalıştırma

### Ön Gereksinimler
*   Python 3.11+
*   Node.js 18+ (Yarn)
*   PostgreSQL (Opsiyonel, yerel geliştirme için SQLite varsayılandır)

### Kurulum Adımları

> **Not (Prod/Staging / CI_STRICT):**
> - `ENV=prod|staging` veya `CI_STRICT=1` iken `DATABASE_URL` **zorunludur** ve **sqlite URL** kabul edilmez.
> - `SYNC_DATABASE_URL` resmi isimdir. Eski `DATABASE_URL_SYNC` yalnızca backward-compat içindir.

1.  **Backend Kurulumu:**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2.  **Frontend Kurulumu:**
    ```bash
    cd frontend
    yarn install
    ```

3.  **Veritabanı Hazırlığı (Migration):**
    ```bash
    cd backend
    alembic upgrade head
    ```

4.  **Servisleri Başlatma (Supervisor ile):**
    Proje kök dizininde:
    ```bash
    sudo supervisorctl start all
    ```
    Veya manuel olarak:
    *   Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8001`
    *   Frontend: `yarn start` (Port 3000)

---

## 🧪 Test ve Doğrulama

Sistem, "Release Gates" adı verilen katı kurallarla korunur. Canlıya çıkmadan önce aşağıdaki testler çalıştırılmalıdır:

### 1. E2E Smoke Test (Release Matrix)
Tüm kritik iş akışlarını (Para yatırma, Poker, Bonus, Risk) tek seferde test eder:
```bash
python3 /app/scripts/release_smoke.py
```

### 2. Migration Kontrolü
Veritabanı şemasının kod ile uyumlu olduğunu doğrular:
```bash
python3 /app/scripts/ci_schema_guard.py
```

### 3. Deploy Preflight
Canlıya çıkış öncesi son kontroller (Env değişkenleri, DB bağlantısı):
```bash
python3 /app/scripts/deploy_preflight.py
```

---

## 🛠️ Operasyonel Kılavuzlar (Runbooks)

Kritik durumlarda ne yapılması gerektiği `/app/artifacts/production_readiness/runbooks/` altında detaylandırılmıştır:

*   **Incident Response:** Sistem çökerse veya saldırı altındaysa izlenecek adımlar.
*   **Rollback Procedure:** Hatalı bir güncelleme nasıl geri alınır.
*   **Reconciliation Playbook:** Ödeme sağlayıcı ile kasa arasında fark çıkarsa nasıl çözülür.

### İzleme (Observability)
Sistem, yapılandırılmış (structured) loglar üretir.
*   **Hata Logları:** `/var/log/supervisor/backend.err.log`
*   **Erişim Logları:** `/var/log/supervisor/backend.out.log`
*   **Alerting:** `AlertEngine` script'i düzenli aralıklarla çalışarak ödeme başarı oranlarını ve risk sinyallerini izler.

---

## 🔒 Güvenlik

*   **Immutable Ledger:** Finansal kayıtlar asla silinemez veya güncellenemez. Sadece ters kayıt (reversal) atılabilir.
*   **RBAC:** Admin rolleri (Owner, Tenant Admin, Support) kesin çizgilerle ayrılmıştır.
*   **Audit Trail:** Tüm admin işlemleri `auditevent` tablosunda kayıt altına alınır.

---

**Sürüm:** 1.0.0 (Production Ready)
**İletişim:** Ops Ekibi
