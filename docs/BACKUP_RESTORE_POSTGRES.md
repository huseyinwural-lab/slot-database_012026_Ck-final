# PostgreSQL Backup / Restore (Operasyonel Kılavuz)

> Bu doküman Patch 2 (P1) kapsamında eklendi.
> Hedef: prod ortamında DB yedeği alma / geri yükleme için minimum uygulanabilir yönerge.

## 1) Backup (pg_dump)

```bash
# Örnek: tek dosya (custom format)
pg_dump --format=custom --no-owner --no-acl \
  --dbname "$DATABASE_URL" \
  --file casino_db.dump
```

### Sık kullanılan opsiyonlar
- `--format=custom`: restore için esnek.
- `--no-owner --no-acl`: farklı kullanıcı/rol ile restore’da sürprizleri azaltır.

## 2) Restore (pg_restore)

```bash
# Hedef veritabanı boş olmalı ya da uygun şekilde hazırlanmalı
pg_restore --clean --if-exists --no-owner --no-acl \
  --dbname "$DATABASE_URL" \
  casino_db.dump
```

## 2.1) Restore Tatbikatı (0’dan geri yükleme)

Amaç: Tek kişinin, sıfır DB’den başlayarak restore yapabilmesi.

1) Boş DB oluştur (örnek):
```bash
createdb casino_db
```

2) Migrations (prod/staging):
```bash
alembic upgrade head
```

3) Restore:
```bash
pg_restore --clean --if-exists --no-owner --no-acl \
  --dbname "$DATABASE_URL" \
  casino_db.dump
```

4) Uygulama ready kontrol:
```bash
curl -i http://localhost:8001/api/ready
```

## 3) Pool tuning önerileri

ENV:
- `DB_POOL_SIZE` (default: 5)
- `DB_MAX_OVERFLOW` (default: 10)

Öneri (başlangıç):
- Küçük trafik: 5 / 10
- Orta trafik: 10 / 20
- Yüksek trafik: DB limitlerine göre ayarlanmalı (max connections).

## 4) Basit doğrulama

```bash
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM tenant;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM adminuser;"
```

## Notlar
- Eğer prod’da yönetilen DB (RDS/CloudSQL) kullanılıyorsa, sağlayıcının snapshot mekanizması tercih edilebilir.
- Yedekleme/restore işleminden sonra `alembic_version` tablosunu kontrol edin:
  ```bash
  psql "$DATABASE_URL" -c "SELECT * FROM alembic_version;"
  ```
