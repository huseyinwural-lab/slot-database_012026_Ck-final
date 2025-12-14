# Dev vs Prod Compose Diff (P2-TCK-101)

Bu doküman, `docker-compose.yml` (dev) ile `docker-compose.prod.yml` (prod) arasındaki kritik farkları özetler.

## Dev Compose (docker-compose.yml)
- Amaç: hızlı geliştirme
- Özellikler:
  - Backend bind-mount: `./backend:/app`
  - Frontend dev server: `yarn start`
  - DEBUG=True
  - LOG_FORMAT=plain

## Prod Compose (docker-compose.prod.yml)
- Amaç: prod benzeri stabil çalıştırma
- Özellikler:
  - Backend `Dockerfile.prod` ile build (uvicorn `--reload` yok)
  - Frontend’ler nginx ile static serve
  - Healthcheck:
    - backend: `/api/health`
    - backend readiness: `/api/health` + `/api/readiness` + `/api/ready`
  - ENV=prod, LOG_FORMAT=json
  - Bind-mount yok

## Acceptance Checklist
- [ ] Prod compose içinde backend service altında `volumes:` yok
- [ ] Backend CMD’de `--reload` yok (`backend/Dockerfile.prod`)
- [ ] `docker compose -f docker-compose.prod.yml up --build` sonrası:
  - [ ] backend healthy
  - [ ] `/api/health` 200
  - [ ] `/api/ready` 200

## Önerilen Diff Komutu
```bash
diff -u docker-compose.yml docker-compose.prod.yml | less
```
