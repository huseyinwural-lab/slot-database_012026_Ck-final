# DR Kontrol Listesi (03:00 Operatörü) (P4.1)

> Bir olay sırasında bu sayfayı kullanın. Kasıtlı olarak kısa ve komut odaklıdır.

Rol ataması (kim ne yapar):
- **Olay Komutanı (IC):** kararları + zaman çizelgesini yönetir
- **Ops/Müdahale Eden:** komutları çalıştırır + çıktıları toplar
- **İletişim sahibi:** paydaşları günceller

Referanslar:
- Runbook: `docs/ops/dr_runbook.md`
- RTO/RPO hedefleri: `docs/ops/dr_rto_rpo.md`
- Kanıt şablonu (kanonik): `docs/ops/restore_drill_proof/template.md`
- Log şeması sözleşmesi: `docs/ops/log_schema.md`

---

## 1) Olayı ilan et

1) Şiddeti ve sorumluyu belirleyin:
- Şiddet: SEV-1 / SEV-2 / SEV-3
- Olay komutanı (IC): <name>
- İletişim sahibi: <name>

2) Zaman damgalarını kaydedin:
- `incident_start_utc`: `date -u +%Y-%m-%dT%H:%M:%SZ`

3) Bir kanıt dosyası oluşturun:
- Kopyalayın: `docs/ops/restore_drill_proof/template.md` → `docs/ops/restore_drill_proof/YYYY-MM-DD.md`
- Üst kısımda **INCIDENT PROOF** olarak işaretleyin.

---

## 2) Kontrol altına alma

Uygun olanı seçin:

### A) Bakım modu / trafiği durdurma
- **K8s:** sıfıra ölçekleyin (en hızlı kontrol altına alma)```bash
  kubectl scale deploy/frontend-admin --replicas=0
  kubectl scale deploy/backend --replicas=0
  ```- **Compose/VM:** stack’i durdurun (veya en azından backend’i)```bash
  docker compose -f docker-compose.prod.yml stop backend frontend-admin
  ```### B) Yönetici girişini dondurma (opsiyonel)
Bir kill-switch/feature flag’iniz varsa etkinleştirin.
Mevcut değilse N/A olarak değerlendirin.

---

## 3) Senaryoyu belirleyin (birini seçin)

- [ ] **Senaryo A (Yalnızca uygulama):** UI/API bozuk, DB muhtemelen sağlıklı.
- [ ] **Senaryo B (DB sorunu):** bozulma / hatalı migrasyon / şema uyuşmazlığı / veri kaybı.
- [ ] **Senaryo C (Altyapı kaybı):** node/host down (VM host kaybı veya K8s node/bölge).

Ardından `docs/ops/dr_runbook.md` içindeki ilgili runbook bölümüne geçin.

---

## 4) Uygula (komutlar)

### Ortak hızlı sinyaller
- Sürüm:```bash
  curl -fsS -i <URL>/api/version
  ```- Sağlık/ready:```bash
  curl -fsS -i <URL>/api/health
  curl -fsS -i <URL>/api/ready
  ```### Senaryo A: Yalnızca uygulama (uygulama imajını geri al)
- **K8s:**```bash
  kubectl rollout undo deploy/backend
  kubectl rollout status deploy/backend
  kubectl rollout undo deploy/frontend-admin
  kubectl rollout status deploy/frontend-admin
  ```- **Compose/VM:**```bash
  # pin previous image tags in docker-compose.prod.yml
  docker compose -f docker-compose.prod.yml up -d
  ```### Senaryo B: DB sorunu (kontrol altına al → değerlendir → geri yükle)
- **Migrasyonları değerlendirin (Alembic kullanılıyorsa):**```bash
  docker compose -f docker-compose.prod.yml exec -T backend alembic current
  ```- **Yedekten geri yükleme (tercih edilen temel çizgi):**```bash
  ./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
  docker compose -f docker-compose.prod.yml restart backend
  ```### Senaryo C: Altyapı kaybı
- **K8s:**```bash
  kubectl get pods -A
  kubectl rollout status deploy/backend
  ```- **VM host kaybı:**
  - Yeni host sağlayın
  - Postgres volume’ünü geri yükleyin (veya yedekten geri yükleyin)
  - Bilinen-iyi imajları yeniden dağıtın

---

## 5) Doğrula (geçilmesi zorunlu)

### API’ler
Bash:```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```Beklenen:
- `/api/health` → 200
- `/api/ready` → 200
- `/api/version` → beklenen

### Owner yetenekleri
Bash:```bash
# 1) Get token (redact password/token in proof)
curl -s -X POST <URL>/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@casino.com","password":"***"}'

# 2) Check capabilities
curl -s <URL>/api/v1/tenants/capabilities -H "Authorization: Bearer ***"
```Beklenen:
- `is_owner=true`

### UI smoke (owner)
- Sonuç: PASS/FAIL
- Adımlar:
  1) Giriş yapın
  2) Tenant listesi yüklenir
  3) Settings → Versions yüklenir
  4) Çıkış çalışır

### Loglar (sözleşme tabanlı)
Log sisteminizi kullanarak, doğrulayın (`docs/ops/log_schema.md` içindeki sözleşme alanlarına göre):
- 5xx oranı düşüyor: `event=request` AND `status_code>=500` filtresi
- gecikme temel çizgiye döner: `duration_ms` için p95
- kalan hataları `request_id` üzerinden ilişkilendirin

---

## 6) Kanıt + Postmortem

1) Kanıt dosyasını (komutlar + çıktılar) doldurun, sırları maskelayın.
2) RTO/RPO ölçümlerini kaydedin (`docs/ops/dr_rto_rpo.md`’ye bakın).
3) Postmortem planlayın:
- kök neden
- düzeltici aksiyonlar
- takipler