# Afet Kurtarma Runbook'u (P4.1)

**Varsayılan kurtarma stratejisi:** yedekten-geri-yükle.

Yol gösterici ilkeler:
- **Veri bütünlüğü > en hızlı kurtarma** (özellikle prod'da).
- DB uyumsuzluğu / hatalı migrasyon için: **izole et → uygulama imajını geri al**, ardından bütünlükten şüphe duyuluyorsa DB'yi geri yükle.
- Kanıt standardı: `docs/ops/restore_drill_proof/template.md`.
- Log doğrulama şu sözleşmeyi kullanır: `docs/ops/log_schema.md`.

Ayrıca bakınız:
- Release karar ağacı: `docs/ops/release.md`
- Yedekleme/geri yükleme: `docs/ops/backup.md`

Operatör giriş noktası:
- 1 sayfalık incident akışını kullanın: `docs/ops/dr_checklist.md`

---

## Küresel önkoşullar (başlamadan önce)

1) Incident kanıt dosyası oluşturun:
- `docs/ops/restore_drill_proof/template.md` dosyasını kopyalayın → `docs/ops/restore_drill_proof/YYYY-MM-DD.md`
- **INCIDENT PROOF** olarak işaretleyin

2) Hedef platforma karar verin (birini seçin):
- **Compose/VM** (docker compose)
- **Kubernetes** (kubectl)

3) Sinyalleri toplayın (çalıştırın ve kanıta yapıştırın)```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```---

## Senaryo A — Yalnızca uygulama arızası (DB OK)

### Tespit
Belirtiler:
- `/api/ready` başarısız olur VEYA artmış 5xx
- DB kontrolleri temizdir (bozulma sinyali yoktur) veya sorunlar uygulama release'i/regresyonuna işaret eder.

Toplanacak sinyaller (kanıta yapıştırın):
- Health/ready:```bash
  curl -i <URL>/api/health
  curl -i <URL>/api/ready
  ```- Sürüm:```bash
  curl -i <URL>/api/version
  ```- Loglar:
  - `event=request` ile filtreleyin ve `status_code>=500` için agregasyon yapın
  - DB'nin erişilebilir olduğunu doğrulayın (bağlantı hatası yok)

### İzolasyon
- **K8s (hızlı):**```bash
  kubectl scale deploy/frontend-admin --replicas=0
  kubectl scale deploy/backend --replicas=0
  ```- **Compose/VM:**```bash
  docker compose -f docker-compose.prod.yml stop backend frontend-admin
  ```### Kurtarma (uygulama imajını geri al)

#### Kubernetes```bash
kubectl rollout undo deploy/backend
kubectl rollout status deploy/backend
kubectl rollout undo deploy/frontend-admin
kubectl rollout status deploy/frontend-admin
```#### Compose/VM```bash
# pin previous image tags in docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```### Doğrulama (mutlaka-geçmeli)```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```Sahip yetkinlikleri:```bash
curl -s <URL>/api/v1/tenants/capabilities -H "Authorization: Bearer ***"
```UI smoke:
- Owner olarak giriş yapın
- Tenants listesini açın
- Settings → Versions
- Çıkış yapın

Loglar:
- 5xx oranının düştüğünü doğrulayın: `event=request` ile filtreleyin ve `status_code>=500` için agregasyon yapın

### Kanıt
- Komut çıktılarını incident kanıt dosyasına yapıştırın.
- RTO'yu kaydedin (bkz. `docs/ops/dr_rto_rpo.md`).

---

## Senaryo B — Hatalı migrasyon / DB uyumsuzluğu

### Tespit
Belirtiler:
- Deploy'u takiben 5xx hataları
- Loglar şema uyumsuzluğunu gösterir (örn. eksik kolonlar/tablolar)
- Alembic sürümü beklenen head'de değil (Alembic kullanılıyorsa)

### İzolasyon
Önce trafiği durdurun.

- **K8s:**```bash
  kubectl scale deploy/backend --replicas=0
  kubectl scale deploy/frontend-admin --replicas=0
  ```- **Compose/VM:**```bash
  docker compose -f docker-compose.prod.yml stop backend frontend-admin
  ```### Kurtarma

#### Adım 1: Uygulama imajını geri alın (baskıyı azaltın)
- **K8s:**```bash
  kubectl rollout undo deploy/backend
  kubectl rollout status deploy/backend
  ```- **Compose/VM:**```bash
  # pin previous backend image tag
  docker compose -f docker-compose.prod.yml up -d backend
  ```#### Adım 2: DB migrasyon durumunu değerlendirin (varsa)
- Compose örneği:```bash
  docker compose -f docker-compose.prod.yml exec -T backend alembic current
  ```Beklenen:
- çıktı, son bilinen iyi migrasyon head'i ile eşleşir.

#### Adım 3: Karar noktası — Hotfix-forward vs Restore

Aşağıdakilerden herhangi biri doğruysa **YEDEKTEN GERİ YÜKLE** seçin:
- Veri bütünlüğü belirsiz
- Uygulama rollback'inden sonra şema uyumsuzluğu devam ediyor
- Kısmi/başarısız migrasyonlardan şüpheleniyorsunuz

Yalnızca şu durumda **HOTFIX-FORWARD** seçin:
- Uyumlu bir migrasyon/uygulama düzeltmesini hızlıca yayımlayabiliyorsanız VE
- Veri bütünlüğünün korunduğundan eminseniz.

#### Adım 4: Yedekten geri yükle (baz çizgi)```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
docker compose -f docker-compose.prod.yml restart backend
```### Doğrulama (mutlaka-geçmeli)```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```DB sağlık kontrolü örnekleri:```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres -d casino_db -c 'select count(*) from tenant;'
```Senaryo A'daki gibi sahip yetkinlikleri + UI smoke.

Loglar:
- 5xx oranının düştüğünü ve gecikmenin normale döndüğünü doğrulayın.

### Kanıt
- Şunları ekleyin:
  - çalıştırılan rollback komutları
  - alembic current çıktısı (veya N/A)
  - restore komutu çıktısı
  - doğrulama çıktıları

---

## Senaryo C — Host/Node kaybı (VM host kaybı veya K8s node/bölge kesintisi)

### Tespit
- Pod'lar schedule edilemiyor / node NotReady / kalıcı depolama kullanılamıyor
- VM host kapalı, volume eksik veya ağ arızası

### İzolasyon
- Split-brain write'ları önlemek için trafiğin durdurulduğundan emin olun (ingress/replicas=0).

### Kurtarma

#### Kubernetes (node kaybı)
1) Cluster durumunu kontrol edin:```bash
kubectl get nodes
kubectl get pods -A
```2) Stateful servislerin (Postgres) depolamaya sahip olduğundan emin olun:
- Postgres yönetilen (managed) ise: sağlayıcı snapshot'ları/PITR üzerinden geri yükleyin.
- Postgres cluster içindeyse: PVC/PV'nin bound olduğundan emin olun.

3) Uygulamayı yeniden schedule edin:```bash
kubectl rollout status deploy/backend
kubectl rollout status deploy/frontend-admin
```#### VM / Compose (host kaybı)
1) Yeni host sağlayın.
2) Postgres verisini geri yükleyin:
- Tercihen Postgres volume'ünü snapshot'tan geri yükleyin, VEYA
- P3 restore prosedürünü kullanarak en son mantıksal (logical) yedekten geri yükleyin.
3) Son bilinen iyi imajları deploy edin:```bash
docker compose -f docker-compose.prod.yml up -d
```### Doğrulama (mutlaka-geçmeli)
Senaryo A ile aynı doğrulama:```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```Sahip yetkinlikleri + UI smoke.

### Kanıt
- Uygulanan altyapı kurtarma adımlarını ve nihai doğrulama çıktılarını ekleyin.

---

## Olay sonrası

1) RTO/RPO'yu kaydedin (bkz. `docs/ops/dr_rto_rpo.md`).
2) Temel logları sözleşme alanlarına göre yakalayın (`request_id`, `path`, `status_code`, `duration_ms`).
3) Postmortem dokümanı oluşturun (kök neden + aksiyonlar + sahipler + son tarihler).