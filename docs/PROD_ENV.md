# Production Environment Variables (Canonical)

Bu doküman Patch 2 kapsamında "prod" için **tek canonical format** tanımlar.

## Canonical Format

### CORS_ORIGINS
Prod ortamında **CSV (virgüllü)** allowlist kullanın:

```bash
CORS_ORIGINS=https://admin.example.com,https://tenant.example.com
```

> JSON list formatı (örn: `["..."]`) dev/legacy uyumluluk için desteklenir; ancak prod için önerilen ve dokümante edilen canonical format CSV'dir.

## Required (prod/staging)
- `ENV=prod` (veya staging)
- `DATABASE_URL=postgresql+asyncpg://...`
- `JWT_SECRET=<strong-random>`
- `CORS_ORIGINS=<csv>`

## Optional
- `DB_POOL_SIZE=5`
- `DB_MAX_OVERFLOW=10`
- `JWT_ALGORITHM=HS256`
