# Quickstart (EN) — 30 minutes

**Last reviewed:** 2026-01-04  
**Owner:** Platform Engineering  

Goal: bring the system up locally in ~30 minutes and prove basic health with a deterministic smoke check.

> EN is the source of truth. TR mirror: `/docs/new/tr/guides/quickstart.md`.

---

## 1) System requirements

- **OS**: macOS / Linux recommended (Windows works with WSL2)
- **Python**: 3.11+
- **Node.js**: 18+
- **Yarn**
- **Docker Desktop**: latest stable
- **Docker Compose**: v2

Optional:
- `curl`

---

## 2) Minimum environment configuration

This repo provides example files:
- `.env.example` (repo root)
- `backend/.env.example`
- `frontend/.env.example`
- `frontend-player/.env.example`

Minimal approach (local):

1) Copy examples:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp frontend-player/.env.example frontend-player/.env
```

2) Fill only the minimum required values:
- `DATABASE_URL` (PostgreSQL for prod/stage; local may run SQLite depending on config)
- Any required JWT/webhook secrets for the flow you want to test

> Note: for production, do NOT rely on `.env` files. Use a secret manager.

---

## 3) Local run (backend + frontend + db)

### Option A — Docker Compose (recommended)
From repo root:

```bash
docker-compose up --build
```

Expected:
- Admin UI: http://localhost:3000
- Player UI: http://localhost:3001
- API docs: http://localhost:8001/docs

### Option B — Non-docker (dev workflow)
See:
- `/docs/new/en/guides/install.md`

---

## 4) Smoke test (single command)

This is a lightweight smoke (no DB destructive actions):

```bash
curl -sS http://localhost:8001/health || curl -sS http://localhost:8001/api/health
```

If your environment does not expose `/health`, use `/docs` as an availability check:

```bash
curl -sS -I http://localhost:8001/docs | head -n 1
```

---

## 5) Most common errors (fast fixes)

1) **Admin login: "Network Error"**
- Check browser DevTools → Network and confirm requests go to `/api/...` (same-origin) and not `localhost:8001` with wrong protocol.

2) **CI/local: `Your lockfile needs to be updated`**
```bash
cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..
```
Commit only `frontend/yarn.lock`.

3) **Migrations fail**
- Check `DATABASE_URL` is correct.
- Run:
```bash
cd backend
alembic upgrade head
```

4) **Port in use**
- 3000/3001/8001 conflicts: stop other dev servers.

5) **Missing env**
- Compare your `.env` against `*.env.example`.

---

## 6) Next step

After quickstart, proceed to:
- `/docs/new/en/guides/ops-manual.md` (real-world operations)
- `/docs/new/en/guides/user-manual.md` (hub)
