# Prod Compose Acceptance Runbook (P2-TCK-101)

Bu runbook, `docker-compose.prod.yml` ile **prod benzeri** ayağa kaldırma ve acceptance doğrulaması içindir.

> Not: Emergent gibi bazı ortamlarda Docker-in-Docker kısıtlı olabilir.
> Bu durumda doğrulama, kendi makinenizde/CI’da çalıştırılarak yapılmalıdır.

---

## 1) Amaç / Kabul Kriterleri

- `docker compose -f docker-compose.prod.yml up --build` ile servisler stabil kalkmalı.
- **Reload yok** (uvicorn `--reload` kullanılmamalı).
- **Bind-mount yok** (volumes altında source code mount edilmemeli).
- Healthcheck:
  - `GET /api/health` → 200
  - `GET /api/ready` → 200

---

## 2) Beklenen Container’lar / Portlar

`docker-compose.prod.yml` servisleri:
- `postgres` → internal 5432 (hosta publish edilmez)
- `backend` → `8001:8001`
- `frontend-admin` → `3000:80`
- `frontend-player` → `3001:80`

---

## 3) Gerekli Environment Variables (Örnek)

Önerilen canonical format: CSV allowlist.

```bash
export ENV=prod
export DATABASE_URL='postgresql+asyncpg://postgres:<PASSWORD>@postgres:5432/casino_db'
export JWT_SECRET='<strong-random>'
export CORS_ORIGINS='https://admin.example.com,https://tenant.example.com'
export LOG_LEVEL='INFO'
export LOG_FORMAT='json'
export DB_POOL_SIZE='5'
export DB_MAX_OVERFLOW='10'

export REACT_APP_BACKEND_URL='http://localhost:8001'
export VITE_API_URL='http://localhost:8001/api/v1'
```

---

## 4) Prod Compose ile Ayağa Kaldırma

```bash
docker compose -f docker-compose.prod.yml up --build
```

Beklenen: servisler healthcheck’ten geçip “healthy” görünmeli.

---

## 5) Smoke / Healthcheck Doğrulaması

### 5.1 Health
```bash
curl -i http://localhost:8001/api/health
```
Beklenen örnek:
```json
{"status":"healthy","environment":"prod"}
```

### 5.2 Ready
```bash
curl -i http://localhost:8001/api/ready
```
Beklenen örnek:
```json
{"status":"ready","dependencies":{"database":"connected"}}
```

---

## 6) “Reload yok” doğrulaması

Prod backend `Dockerfile.prod` ile çalışır ve CMD’de `--reload` yoktur.
Kontrol:
- `docker logs <backend_container>` içinde `Started reloader process` benzeri bir ifade olmamalı.

---

## 7) “Bind-mount yok” doğrulaması

Prod compose dosyasında backend altında `volumes: - ./backend:/app` gibi mount’lar olmamalı.
Kontrol:
- `docker-compose.prod.yml` içinde `backend` service altında `volumes:` bulunmamalı.

---

## 8) Dev vs Prod compose fark analizi (Diff)

- Dev compose (`docker-compose.yml`) şunları içerir:
  - bind-mount volumes
  - dev frontend start
  - DEBUG=True
- Prod compose (`docker-compose.prod.yml`) şunları içerir:
  - nginx static serve
  - reload yok
  - healthcheck
  - ENV=prod + LOG_FORMAT=json

Önerilen komut:
```bash
diff -u docker-compose.yml docker-compose.prod.yml | less
```

---

## 9) Olası Sorunlar

- `DATABASE_URL` host/port yanlışsa `/api/ready` 503 döner.
- `JWT_SECRET` boşsa (prod/staging) backend fail-fast ile başlamaz.
- CORS allowlist yanlışsa browser preflight 400 (Disallowed CORS origin) görürsünüz.
