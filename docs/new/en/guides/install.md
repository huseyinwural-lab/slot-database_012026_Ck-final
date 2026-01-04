# Install Guide (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Platform Engineering  

This guide explains how to run the project locally for development and how to start the full stack using Docker.

---

## 1) Prerequisites

- **Python:** 3.11+
- **Node.js:** 18+
- **Yarn** (recommended)
- **Docker Desktop** (optional but recommended)

---

## 2) Run with Docker (recommended)

From repo root:

```bash
docker-compose up --build
```

Services:
- Admin Panel: http://localhost:3000
- Player Lobby: http://localhost:3001
- Backend API docs: http://localhost:8001/docs

---

## 3) Run locally (developer workflow)

### Backend

```bash
cd backend
python -m venv venv
# Mac/Linux
source venv/bin/activate
# Windows
# venv\Scripts\activate

pip install -r requirements.txt
```

Run (example):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend (admin)

```bash
cd frontend
yarn install
yarn start
```

### Frontend (player)

```bash
cd frontend-player
yarn install
yarn dev
```

---

## 4) Database

- **Production:** PostgreSQL
- **Local dev (varies by configuration):** SQLite or PostgreSQL

If you use PostgreSQL locally, make sure migrations are applied:

```bash
cd backend
alembic upgrade head
```

---

## 5) Common issues

### “Your lockfile needs to be updated” (CI / frozen lockfile)
This means `frontend/package.json` and `frontend/yarn.lock` are out of sync.

Fix (run from repo root):

```bash
cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..

git status
# Expect: only frontend/yarn.lock changed
```

Commit only `frontend/yarn.lock`.

### Admin login “Network Error”
Usually indicates frontend API baseURL points to a wrong host/protocol. Check the request target in DevTools Network.

Legacy deep-dive docs:
- `/docs/TENANT_ADMIN_FLOW.md`
- `/docs/ops/reverse-proxy/*`
