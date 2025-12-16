# CI: Prod Compose Acceptance (GitHub Actions)

Bu doküman, `P2-TCK-101` ve `P2-TCK-104` acceptance testlerini CI’da koşturan workflow’u açıklar.

## Workflow dosyası
- Path: `.github/workflows/prod-compose-acceptance.yml`

## Ne garanti eder?
- **Fresh start**: `docker compose down -v` ile boş Postgres volume.
- **P2-TCK-101**: prod compose stack ayağa kalkar; `GET /api/health` ve `GET /api/ready` 200.
- **P2-TCK-104 (pratik idempotency)**: backend restart sonrası tekrar health/ready 200.

## Önemli uyarlamalar

### 1) API_BASE portu
Bu repoda prod compose backend: `8001:8001`.
Workflow:
- `API_BASE=http://localhost:8001`

Eğer ileride port değişirse güncelleyin.

### 2) DB servis adı
Bu repoda prod compose db servisi adı: `postgres`.
Workflow DATABASE_URL:
- `postgresql+asyncpg://postgres:postgres@postgres:5432/casino_db`

### 3) Secret yönetimi
CI’da dummy secret yeterli; prod’da GitHub Secrets kullanın:
- `JWT_SECRET`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`

## Fail durumunda loglar
Workflow failure olduğunda:
- `docker compose ps`
- `docker compose logs --tail=300`
çıktıları job loguna basılır.
