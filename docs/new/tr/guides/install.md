# Kurulum Rehberi (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Platform Engineering  

Bu rehber, projeyi yerelde geliştirme amacıyla çalıştırmayı ve Docker ile tüm stack’i ayağa kaldırmayı anlatır.

---

## 1) Ön gereksinimler

- **Python:** 3.11+
- **Node.js:** 18+
- **Yarn** (önerilir)
- **Docker Desktop** (opsiyonel ama önerilir)

---

## 2) Docker ile çalıştırma (önerilen)

Repo kök dizininde:

```bash
docker-compose up --build
```

Servisler:
- Admin Panel: http://localhost:3000
- Player Lobby: http://localhost:3001
- Backend API docs: http://localhost:8001/docs

---

## 3) Lokal çalıştırma (developer akışı)

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

Çalıştırma (örnek):

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

## 4) Veritabanı

- **Prod:** PostgreSQL
- **Local dev (konfigürasyona göre):** SQLite veya PostgreSQL

PostgreSQL kullanıyorsan migration:

```bash
cd backend
alembic upgrade head
```

---

## 5) Sık sorunlar

### “Your lockfile needs to be updated” (CI / frozen lockfile)
Bu, `frontend/package.json` ile `frontend/yarn.lock` senkron değil demektir.

Çözüm (repo kökünden):

```bash
cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..

git status
# Beklenen: sadece frontend/yarn.lock değişmiş olmalı
```

Sadece `frontend/yarn.lock` commit edilmeli.

### Admin login “Network Error”
Genellikle frontend’in API baseURL’i yanlış host/protokole gidiyordur. DevTools → Network’ten request URL’yi kontrol et.

Legacy referans:
- `/docs/TENANT_ADMIN_FLOW.md`
- `/docs/ops/reverse-proxy/*`
