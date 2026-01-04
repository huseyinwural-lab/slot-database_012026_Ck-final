# Üretim Dağıtım Kılavuzu (Tek VM + Docker Compose)

Hedef varsayım:
- **Tek Ubuntu VM (22.04 / 24.04)**
- **Docker Engine + Docker Compose v2**
- **Let's Encrypt** TLS ile harici ters proxy (**Nginx veya Traefik**) (TLS harici proxy’de sonlanır; UI container’larına giden upstream trafik düz HTTP’dir)
- İki ayrı origin:
  - Admin UI: `https://admin.domain.tld`
  - Player UI: `https://player.domain.tld`

Bu doküman **tek, uçtan uca bir runbook** olarak tasarlanmıştır: yeni bir operatör sistemi sıfırdan ayağa kaldırabilmelidir.

---

## 1) Ön Koşullar (P1-DEPLOY-001)

### İşletim Sistemi
- Ubuntu 22.04 LTS veya 24.04 LTS

### Docker
Önerilen minimumlar:
- Docker Engine: 24+ (CI daha yeni sürümler kullanır; modern herhangi bir Docker çalışmalıdır)
- Docker Compose eklentisi (v2): 2.20+

Doğrulama:```bash
docker version
docker compose version
```### DNS
VM’ye işaret eden DNS kayıtlarını oluşturun:
- `admin.domain.tld` -> VM public IP
- `player.domain.tld` -> VM public IP

### TLS / Ters proxy
Birini seçin:
- Nginx + Certbot (HTTP-01)
- ACME (Let's Encrypt) ile Traefik

---

## 2) Repo düzeni ve portlar (P1-DEPLOY-001)

Üst düzey harita:
- `backend` (FastAPI) **8001** üzerinde dinler (container portu 8001, prod compose’ta host publish 8001)
- `frontend-admin` admin UI’yi **3000** üzerinde sunar (container portu 80, host publish 3000)
- `frontend-player` player UI’yi **3001** üzerinde sunar (container portu 80, host publish 3001)
- `postgres` dahili 5432 (docker volume ile kalıcı)

Önemli yönlendirme modeli:
- Tarayıcılar aynı-origin API path’lerini çağırır:
  - `https://admin.domain.tld/api/v1/...`
  - `https://player.domain.tld/api/v1/...`
- UI container’larının dahili Nginx proxy’leri `location /api/` -> `proxy_pass http://backend:8001;` (Docker ağı).
- **Harici** ters proxy, same-origin’i korumak için `location /api/` isteklerini (doğrudan backend’e değil) UI container’ına iletmelidir.
- Path işleme kuralı: `/api/v1/...` yolunu olduğu gibi koruyun (sondaki slash rewrite hatalarından kaçının).

---

## 3) İlk kurulum (P1-DEPLOY-001)

### 3.1 Ortam (env) dosyaları
Env dosyalarını oluşturun (commit etmeyin):
- Kök: `/.env` (docker compose tarafından kullanılır)
- Backend: `/backend/.env` (backend’i compose dışında çalıştırırsanız; opsiyonel)
- Frontend şablonları prod compose’ta build arg’dır; tipik olarak yalnızca kök `/.env` gerekir.

Şablonlar sağlanmıştır:
- `/.env.example`
- `/backend/.env.example`
- `/frontend/.env.example`
- `/frontend-player/.env.example`

### 3.2 Gerekli değerler (production)
En azından `/.env` içinde şunları ayarlayın:
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `JWT_SECRET`
- `CORS_ORIGINS`

Önerilen opsiyoneller:
- `LOG_LEVEL=INFO`
- `LOG_FORMAT=auto` (prod/staging varsayılan: json, dev varsayılan: plain)
- `DB_POOL_SIZE=5`
- `DB_MAX_OVERFLOW=10`

### 3.3 Env kontrol listesi + güvenli değer üretimi (P1-DEPLOY-003)

| Değişken | Gerekli | Nasıl üretilir / örnek |
|---|---:|---|
| `JWT_SECRET` | ✅ | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | ✅ | `openssl rand -base64 24` (güvenle saklayın) |
| `CORS_ORIGINS` | ✅ | `https://admin.domain.tld,https://player.domain.tld` |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://postgres:<POSTGRES_PASSWORD>@postgres:5432/casino_db` |

⚠️ **Production’da wildcard yok**: `CORS_ORIGINS` bir allowlist olmalıdır.

### 3.4 Bootstrap (tek seferlik) kuralı (P1-DEPLOY-003)

- Production kuralı: varsayılan olarak `BOOTSTRAP_ENABLED=false`.
- Bootstrap’ı yalnızca ilk kurulum / kontrollü tek seferlik kullanıcı oluşturma için etkinleştirin.

`BOOTSTRAP_ENABLED=true` ayarlarsanız, ayrıca şunları da ayarlamalısınız:
- `BOOTSTRAP_OWNER_EMAIL`
- `BOOTSTRAP_OWNER_PASSWORD`

İlk başarılı girişten sonra `BOOTSTRAP_ENABLED=false` olarak tekrar ayarlayın ve yeniden deploy edin.

---

## 4) Build ve başlatma (Docker Compose)

Repo kök dizininden:```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

docker compose -f docker-compose.prod.yml ps
```---

## 5) Migrasyonlar

Migrasyonlar backend container’ı başlangıcında çalışır.

Kontrol edin:```bash
docker compose -f docker-compose.prod.yml logs --no-color --tail=200 backend
```---

## 6) Ters proxy

Kopyala-yapıştır örnekleri:
- Nginx: `docs/reverse-proxy/nginx.example.conf`
- (Opsiyonel) Traefik: `docs/reverse-proxy/traefik.example.yml`

### WebSocket notu (opsiyonel)
WebSocket bugün gerekli değil. İleride WS eklerseniz, ters proxy’nin şunları içerdiğinden emin olun:
- `Upgrade` / `Connection` header’ları
- makul read/write timeout’ları

---

## 7) Smoke test (2 dakika) (P1-DEPLOY-005)

### 7.1 Container’lar```bash
docker compose -f docker-compose.prod.yml ps
```### 7.2 Backend sağlık kontrolü```bash
curl -fsS http://127.0.0.1:8001/api/health
curl -fsS http://127.0.0.1:8001/api/ready
# (optional) provide your own correlation ID
curl -fsS -H 'X-Request-ID: ABCdef12_-' http://127.0.0.1:8001/api/health -D - | head
```### 7.3 Login doğrulaması (curl)
Auth’u doğrudan doğrulayabilirsiniz (değerleri değiştirin):```bash
API_BASE=http://127.0.0.1:8001
curl -sS -o /tmp/login.json -w "%{http_code}" \
  -X POST "${API_BASE}/api/v1/auth/login" \
  -H 'content-type: application/json' \
  --data '{"email":"admin@casino.com","password":"Admin123!"}'
cat /tmp/login.json
```### 7.4 Ters proxy kontrolü
Bir tarayıcıdan:
- `https://admin.domain.tld/login` adresini açın
- Girişin çalıştığını doğrulayın.
- DevTools Network’te istekler şuraya gitmelidir:
  - `https://admin.domain.tld/api/...` (aynı origin)
  - doğrudan `:8001`’e **DEĞİL**

---

## 8) Loglar

`ENV=prod|staging` ortamında loglar varsayılan olarak JSON’dur (`LOG_FORMAT=auto`).
Her yanıt, ilişkilendirme (correlation) için `X-Request-ID` içerir.```bash
docker compose -f docker-compose.prod.yml logs --no-color --tail=300

docker compose -f docker-compose.prod.yml logs --no-color --tail=300 backend
```---

## 9) Yedekleme / Geri Yükleme / Geri Alma (Rollback) (P1-DEPLOY-004)

## 9.1) Denetim (audit) saklama süresi
Bkz: `docs/ops/audit_retention.md` (90 günlük saklama + temizleme (purge) script’i)

Birincil doküman:
- `docs/ops/backup.md`

Script’ler (opsiyonel kolaylık):
- `./scripts/backup_postgres.sh`
- `./scripts/restore_postgres.sh <backup.sql.gz>`

Hızlı yedekleme:```bash
./scripts/backup_postgres.sh
```Hızlı geri yükleme:```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
```Geri alma (rollback) yönergesi:
- Versiyonlanmış image tag’lerini tercih edin.
- Önceki, bilinen-iyi (known-good) image tag’ini yeniden deploy ederek geri alın.
- Veri bozulması için: DB’yi yedekten geri yükleyin + önceki image’ı yeniden deploy edin.