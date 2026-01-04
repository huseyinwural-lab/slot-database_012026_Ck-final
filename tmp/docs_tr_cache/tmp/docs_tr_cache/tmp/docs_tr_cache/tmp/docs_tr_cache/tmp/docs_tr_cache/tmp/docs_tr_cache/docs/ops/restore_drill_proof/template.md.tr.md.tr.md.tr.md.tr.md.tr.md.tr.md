# Geri Yükleme Tatbikatı Kanıtı — YYYY-MM-DD

## Bağlam

> Redaksiyon gerekli: Sırları commit etmeyin. Token/parola/anahtar ve kimlik bilgisi içeren URL’leri maskeleyin.
> Hassas değerler için `***` kullanın.

- Ortam: staging / production / prod-compose
- Operatör: <name>
- Yedek Artefaktı:
  - Yerel: /var/lib/casino/backups/<backup_id>.dump
  - veya S3: s3://<bucket>/<path>/<backup_id>.dump
- Hedef Veritabanı: <host:port/dbname>
- Beklenen Uygulama Sürümü: <örn. 0.1.0>

## Geri yükleme öncesi
- Bakım modu etkin: evet/hayır
- Geri yükleme öncesi anlık görüntü/yedek alındı: evet/hayır (detaylar)

## Geri Yükleme Yürütümü

Komut:```bash
./scripts/restore_postgres.sh ...
```Çıktı (tail):```text
<paste output>
```## Backend kontrolleri

### /api/health
Bash:```bash
curl -i <URL>/api/health
```Metin:```text
<paste output>
```### /api/ready
Bash:```bash
curl -i <URL>/api/ready
```Metin:```text
<paste output>
```### /api/version
Bash:```bash
curl -s <URL>/api/version
```Json:```json
{ "service": "backend", "version": "<expected>", "git_sha": "____", "build_time": "____" }
```### Kimlik Doğrulama / Yetenekler
Bash:```bash
curl -s <URL>/api/v1/tenants/capabilities -H "Authorization: Bearer ***"
```Json:```json
{ "is_owner": true }
```## Veritabanı Tutarlılık Kontrolü

### Alembic head/current
Bash:```bash
alembic current
```Metin:```text
<paste output>
```### Temel sayımlar
Bash:```bash
psql "$DATABASE_URL" -c "select count(*) from tenants;"
psql "$DATABASE_URL" -c "select count(*) from admin_users;"
```Metin:```text
<paste output>
```## UI Smoke (Sorumlu)
- Sonuç: BAŞARILI/BAŞARISIZ
- Notlar: <herhangi bir anomali>

## Sonuç
- Geri yükleme tatbikatı sonucu: BAŞARILI/BAŞARISIZ
- Takip aksiyonları: <liste>