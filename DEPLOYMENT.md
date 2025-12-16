# Production Deployment (Staging / Release-Ready)

Target assumption: **Single Ubuntu VM** running **Docker Compose** with an external reverse proxy (**Nginx or Traefik**) and **Let's Encrypt** SSL.

## 1) Prerequisites
- Ubuntu (recommended LTS)
- Docker + Docker Compose plugin
- A domain name pointing to the VM (A/AAAA records)
- External reverse proxy (Nginx/Traefik) terminating TLS

## 2) Environment variables
Create a production env file (do not commit it). Use the repo templates:
- `/.env.example`
- `/backend/.env.example`
- `/frontend/.env.example`
- `/frontend-player/.env.example`

Minimum required in production:
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `JWT_SECRET`
- `CORS_ORIGINS`

Bootstrap (optional, one-shot):
- `BOOTSTRAP_ENABLED=false` by default
- If you set `BOOTSTRAP_ENABLED=true`, you must also set:
  - `BOOTSTRAP_OWNER_EMAIL`
  - `BOOTSTRAP_OWNER_PASSWORD`

## 3) Build & start (Docker Compose)
From repo root:
- Build:
  - `docker compose -f docker-compose.prod.yml build`
- Start:
  - `docker compose -f docker-compose.prod.yml up -d`
- Status:
  - `docker compose -f docker-compose.prod.yml ps`

## 4) Migrations
Migrations are executed on backend container startup (see backend start script / logs). To verify:
- Check backend logs:
  - `docker compose -f docker-compose.prod.yml logs --tail=200 backend`

## 5) Health checks
- Backend health:
  - `GET /api/health`
- Backend readiness:
  - `GET /api/ready`

If you are using an external reverse proxy:
- Route `https://<admin-domain>/` -> `frontend-admin` container (port 80)
- Route `https://<player-domain>/` -> `frontend-player` container (port 80)

## 6) Reverse proxy expectations (important)
The frontend containers include an Nginx config that proxies API calls same-origin:
- Browser calls: `https://<origin>/api/...`
- Container Nginx proxies: `/api/` -> `http://backend:8001`

This avoids browsers calling backend port `:8001` directly.

## 7) Logs
- Compose logs:
  - `docker compose -f docker-compose.prod.yml logs --no-color --tail=300`
- Specific service:
  - `docker compose -f docker-compose.prod.yml logs --no-color --tail=300 backend`

## 8) Backup / restore (recommended baseline)
Postgres backup example:
- Backup:
  - `docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres -d casino_db | gzip > backup.sql.gz`
- Restore (dangerous / overwrite):
  - `gunzip -c backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d casino_db`

Retention suggestion:
- Daily backups + 7-30 day retention (cron + rotation)

## 9) Rollback
- Rollback strategy depends on your image/versioning.
- Minimum: keep the previous working image tag and previous `.env`.
- Re-deploy previous compose stack + restart services.
