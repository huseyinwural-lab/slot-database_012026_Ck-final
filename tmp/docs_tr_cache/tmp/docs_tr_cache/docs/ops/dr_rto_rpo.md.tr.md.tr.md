# DR RTO / RPO Hedefleri (P4.1)

## Tanımlar

- **RTO (Recovery Time Objective):** **olay başlangıcından** **servisin yeniden sağlanmasına** (sağlıklı olduğu doğrulanmış) kadar kabul edilebilir en yüksek süre.
- **RPO (Recovery Point Objective):** en son geri yüklenebilir yedekleme noktası ile olay zamanı arasındaki süre olarak ölçülen, kabul edilebilir en yüksek **veri kaybı penceresi**.

## Temel hedefler (mevcut gerçeklik)

Bu hedefler **günlük yedeklemeleri** varsayar (bkz. `docs/ops/backup.md`).

### Staging / Prod-compose
- **RTO:** 60–120 dakika
- **RPO:** 24 saat

### Kubernetes (cluster + manifestler + PVC/Secrets hazırsa)
- **RTO:** 30–60 dakika
- **RPO:** 24 saat

## Opsiyonel iyileştirme hedefi (daha sık yedekleme eklerseniz)

Saatlik yedeklemeler devreye alınırsa:
- **RPO:** 1 saat

## Ölçüm yöntemi (kayıt altına alınmalı)

### RTO ölçümü
Kaydedin:
- `incident_start_utc`: olayın ilan edildiği zaman (bkz. `docs/ops/dr_checklist.md`)
- `recovery_complete_utc`: tüm doğrulama kontrolleri geçtiğinde:
  - `GET /api/health` → 200
  - `GET /api/ready` → 200
  - `GET /api/version` → beklenen
  - sahip yetkinlikleri `is_owner=true` gösterir
  - UI smoke testi geçer

RTO = `recovery_complete_utc - incident_start_utc`

### RPO ölçümü
Kaydedin:
- `backup_timestamp_utc`: kullanılan yedek artefaktının zaman damgası
- `incident_start_utc`

RPO = `incident_start_utc - backup_timestamp_utc`

## Kanıt standardı

Herhangi bir DR olayı (gerçek olay veya tatbikat) için, kanıtı kanonik şablonu kullanarak kaydedin:
- `docs/ops/restore_drill_proof/template.md`

Gizli bilgileri/token’ları `docs/ops/restore_drill.md` uyarınca redakte edin.