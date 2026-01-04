# Denetim Günlüğü Saklama (90 gün)

Bu proje, kanonik denetim olaylarını `AuditEvent` SQLModel’inde saklar.

## Ortamlar / DB ayrımı (SQLite vs Postgres)
- **Dev/local**: genellikle **SQLite** kullanır (`sqlite+aiosqlite:////app/backend/casino.db`).
- **Staging/prod**: **PostgreSQL** kullanması beklenir (`DATABASE_URL` üzerinden).

Temizleme (purge) betiği, `backend/config.py` içinde `settings.database_url` üzerinden **hangi DB yapılandırıldıysa ona** bağlanır.

### Tablo adı
Bu kod tabanında denetim tablo adı **`auditevent`**’tir (SQLModel varsayılan adlandırma). Temizleme aracı ve SQL parçacıkları bunu varsayar.

## Zaman damgası
- Denetim `timestamp`, **UTC** olarak saklanır.
- Temizleme kesim noktası (cutoff) **UTC** olarak hesaplanır ve DB `timestamp` sütununa karşılaştırılır.

## Hedef
- Denetim olaylarını **90 gün** boyunca tutmak
- Sorguların (zamana, kiracıya, eyleme göre) hızlı kalmasını sağlamak
- Operasyonel olarak basit bir temizleme prosedürü sağlamak

## Önerilen İndeksler
### SQLite
SQLite, migration’lar tarafından oluşturulan şu indekslerden zaten fayda sağlar:
- `timestamp`
- `tenant_id`
- `action`
- `actor_user_id`
- `request_id`
- `resource_type`
- `resource_id`

### PostgreSQL (staging/prod)
Yaygın erişim örüntüleri için indeksler oluşturun:```sql
-- time range scans
CREATE INDEX IF NOT EXISTS ix_audit_event_timestamp ON auditevent (timestamp DESC);

-- tenant + time
CREATE INDEX IF NOT EXISTS ix_audit_event_tenant_time ON auditevent (tenant_id, timestamp DESC);

-- action filters
CREATE INDEX IF NOT EXISTS ix_audit_event_action_time ON auditevent (action, timestamp DESC);

-- request correlation
CREATE INDEX IF NOT EXISTS ix_audit_event_request_id ON auditevent (request_id);
```> Postgres’te tabloyu `audit_event` olarak yeniden adlandırırsanız, SQL’i buna göre ayarlayın.

## Temizleme Stratejisi
### Politika
- **90 günden** eski olayları silin.
- Düşük trafik saatlerinde en az **günlük** çalıştırın.

### Betik ile temizleme (önerilen)
`scripts/purge_audit_events.py` kullanın:```bash
# Dry-run (no deletes) – prints JSON summary
python scripts/purge_audit_events.py --days 90 --dry-run

# Batch delete (default batch size is 5000)
python scripts/purge_audit_events.py --days 90 --batch-size 5000
```### Konteyner içinde çalıştırma (compose örneği)
Docker Compose ile çalıştırılıyorsa, backend konteyneri içinde yürütün:```bash
docker compose exec backend python /app/scripts/purge_audit_events.py --days 90 --dry-run
```### Cron örneği
Her gün 03:15’te çalıştırın:```cron
15 3 * * * cd /opt/casino-admin && /usr/bin/python3 scripts/purge_audit_events.py --days 90 >> /var/log/casino-admin/audit_purge.log 2>&1
```## Güvenlik Notları
- Temizleme **geri alınamaz**.
- DB yedeklerini saklayın (bkz. `docs/ops/backup.md`).
- Temizleme betiği yalnızca `timestamp < cutoff` koşuluna göre siler.

## Doğrulama
Bir temizlemeden sonra:
- Kalan satır sayısını sorgulayın (isteğe bağlı):```sql
SELECT COUNT(*) FROM auditevent;
```- En son denetim olaylarının API üzerinden hâlâ erişilebilir olduğunu doğrulayın:```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "<BASE_URL>/api/v1/audit/events?since_hours=24&limit=10"
```
