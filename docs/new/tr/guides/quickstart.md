# Quickstart (TR) — 30 dakikada ayağa kaldır

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Platform Engineering  

Hedef: sistemi ~30 dakikada localde ayağa kaldırmak ve deterministik bir smoke check ile temel sağlığı doğrulamak.

> EN ana kaynaktır. TR mirror: `/docs/new/tr/guides/quickstart.md`.

---

## 1) Sistem gereksinimleri

- **OS**: macOS / Linux önerilir (Windows için WSL2)
- **Python**: 3.11+
- **Node.js**: 18+
- **Yarn**
- **Docker Desktop**: güncel stable
- **Docker Compose**: v2

Opsiyonel:
- `curl`

---

## 2) Minimum environment konfigürasyonu

Repo örnek dosyaları:
- `.env.example` (repo kökü)
- `backend/.env.example`
- `frontend/.env.example`
- `frontend-player/.env.example`

Minimal yaklaşım (local):

1) Örnekleri kopyala:
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp frontend-player/.env.example frontend-player/.env
```

2) Minimum gerekli alanları doldur:
- `DATABASE_URL` (prod/stage için PostgreSQL; local config’e göre SQLite olabilir)
- Test etmek istediğin akışa göre JWT/webhook secret’ları

> Not: prod’da `.env` ile yönetim yapılmaz. Secret manager kullanılır.

---

## 3) Local run (backend + frontend + db)

### Seçenek A — Docker Compose (önerilen)
Repo kökünden:

```bash
docker-compose up --build
```

Beklenen:
- Admin UI: http://localhost:3000
- Player UI: http://localhost:3001
- API docs: http://localhost:8001/docs

### Seçenek B — Docker’sız dev akışı
Bkz:
- `/docs/new/tr/guides/install.md`

---

## 4) Smoke test (tek komut)

Hafif smoke (DB’ye yıkıcı işlem yok):

```bash
curl -sS http://localhost:8001/health || curl -sS http://localhost:8001/api/health
```

Eğer ortamında `/health` yoksa, `/docs` ile availability kontrolü:

```bash
curl -sS -I http://localhost:8001/docs | head -n 1
```

---

## 5) En sık hatalar (hızlı çözümler)

1) **Admin login: "Network Error"**
- DevTools → Network: request’lerin `/api/...` (same-origin) gittiğini doğrula.

2) **CI/local: `Your lockfile needs to be updated`**
```bash
cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..
```
Sadece `frontend/yarn.lock` commit edilir.

3) **Migration fail**
- `DATABASE_URL` doğru mu kontrol et.
- Çalıştır:
```bash
cd backend
alembic upgrade head
```

4) **Port çakışması**
- 3000/3001/8001 doluysa diğer servisleri durdur.

5) **Env eksik**
- `.env` dosyanı `*.env.example` ile karşılaştır.

---

## 6) Sonraki adım

Quickstart sonrası:
- `/docs/new/tr/guides/ops-manual.md` (gerçek hayat operasyon)
- `/docs/new/tr/guides/user-manual.md` (hub)
