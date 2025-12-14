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

## 3) Basit doğrulama

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
