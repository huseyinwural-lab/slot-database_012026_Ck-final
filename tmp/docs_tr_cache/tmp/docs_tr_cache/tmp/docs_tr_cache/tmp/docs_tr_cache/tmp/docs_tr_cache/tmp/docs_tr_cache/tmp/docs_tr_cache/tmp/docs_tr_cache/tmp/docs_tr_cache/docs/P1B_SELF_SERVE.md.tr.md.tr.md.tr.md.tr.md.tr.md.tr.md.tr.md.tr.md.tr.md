# P1-B Self-Servis Kanıt Paketi (Harici Postgres + Redis) — Go/No-Go Geçidi

## Amaç
**harici Postgres** ve **harici Redis** ile üretim benzeri hazır olma durumunu doğrulayın:
- Migrasyonlar gerçek Postgres üzerinde sorunsuz uygulanır
- Servis, yalnızca **DB + Redis** gerçekten erişilebilir olduğunda **Ready (200)** olur
- Redis yoksa/erişilemiyorsa, Ready **503** olur (trafik yok)

Bu doküman **URL’siz kanıt paylaşımı** için tasarlanmıştır (gizli bilgileri maskeleyin).

---

## Sözleşme Özeti

### Import-time (fail-fast) — varlık/şekil kontrolleri
`ENV in {staging, prod}` **VEYA** `CI_STRICT=1` olduğunda:
- `DATABASE_URL` ayarlı değil → başlangıç **BAŞARISIZ**
- `DATABASE_URL` sqlite şeması → başlangıç **BAŞARISIZ**
- `REDIS_URL` ayarlı değil → başlangıç **BAŞARISIZ**

### Runtime (Go/No-Go) — gerçek bağlantı kontrolleri
`ENV in {staging, prod}` **VEYA** `CI_STRICT=1` olduğunda:
- `GET /api/ready`
  - DB OK + Redis `PING` OK → **200**
  - Redis erişilemiyor → **503**

---

## Kanıt Maskeleme Kuralları
Log paylaşırken:
- Kimlik bilgilerini `***` ile değiştirin
- Kabul edilebilir maskeleme örnekleri:
  - `postgresql+asyncpg://user:PASS@host:5432/db` → `postgresql+asyncpg://user:***@host:5432/db`
  - `redis://:PASS@host:6379/0` → `redis://:***@host:6379/0`
- Gerekirse host adlarını/IP’leri kısmen maskeleyin, ancak teşhis için yeterli sinyali koruyun (örn. port ve şemayı koruyun).

---

## Adım 1 — Harici Migrasyon Geçidi (Postgres)

### Komutlar```bash
cd /app/backend

export ENV=staging
export CI_STRICT=1
export DATABASE_URL='postgresql+asyncpg://...'
export REDIS_URL='redis://...'

alembic upgrade head
alembic current
```### Geçme Kriterleri
- `alembic upgrade head` **0** ile çıkar
- `alembic current` **head** revizyonunu gösterir

### Paylaşılacak Kanıt (maskeli)
- `alembic upgrade head` çıktısı
- `alembic current` çıktısı

---

## Adım 2 — Runtime Ready Geçidi (DB + Redis)

### Servisi Başlatın
Repo’nun kanonik giriş noktasını kullanın.

Örnekler:

**Dev/self-servis (doğrudan uvicorn):**```bash
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001
```**Prod benzeri container giriş noktası (staging/prod’da migrasyonları çalıştırır):**```bash
/app/scripts/start_prod.sh
```### Ready + Sürümü Kontrol Edin```bash
curl -sS -i http://localhost:8001/api/ready
curl -sS -i http://localhost:8001/api/version
```### Geçme Kriterleri
- `/api/ready` **200** döndürür
- Yanıt, DB’nin bağlı olduğunu ve Redis’in bağlı olduğunu belirtir (alan adları değişebilir; bu repoda `/api/ready` şu anda `dependencies.database|redis|migrations` döndürür)

### Paylaşılacak Kanıt (maskeli)
- `/api/ready` için tam yanıt başlıkları + gövdesi
- `/api/version` çıktısı
- DB bağlantısı + Redis ping için boot log satırları

---

## Adım 3 — Negatif Kanıt (Redis bozuk ⇒ Ready 503)

### Redis URL’sini Bozun```bash
export REDIS_URL='redis://:***@127.0.0.1:1/0'
# restart service if needed
```### Ready’yi Kontrol Edin```bash
curl -sS -i http://localhost:8001/api/ready
```### Geçme Kriterleri
- `/api/ready` **503** döndürür
- Gövde, Redis’e erişilemediğini belirtir

### Paylaşılacak Kanıt
- `/api/ready` yanıtı (maskeli)
- Redis ping hatasını gösteren ilgili log satırları

---

## İsteğe Bağlı Adım 4 — Fail-fast runtime testi (listener yok)
Bu, Redis URL’si eksikse strict modun hızlıca çıktığını doğrular.```bash
cd /app/backend
export ENV=staging
export CI_STRICT=1
unset REDIS_URL
pytest -q tests/test_runtime_failfast_redis_uvicorn.py
```Geçti: test yeşil.

---

## /api/ready için Önerilen Yanıt Formatı
Belirsizliği azaltmak için `/api/ready` makine tarafından okunabilir alanlar içermelidir.

Örnek (önerilen):```json
{
  "status": "ok|fail",
  "checks": {
    "db": {"ok": true, "detail": "connected|unreachable"},
    "redis": {"ok": true, "detail": "connected|unreachable"}
  }
}
```(Tam şema geçit için gerekli değildir, ancak güçlü şekilde önerilir.)

---

## İki küçük ama kritik iyileştirme (önerilir)

1) **`/api/ready` JSON’unu standartlaştırın**
Bugün `dependencies.redis=connected/unreachable` yeterli olsa bile, `status + checks` gibi stabil bir yapı CI/CD’yi ve nöbetçi (on-call) hata ayıklamayı çok daha hızlı hale getirir.

2) **Kısa readiness zaman aşımları**
DB/Redis kontrollerini sınırlı tutun (örn. ~0.5–2s). Allowlist/VPC/DNS hatalarında, asılı kalan bir probe yerine hızlı bir **503** istersiniz.

---

## Sonuç ve Sonraki Adım
Adım 1–3 karşılanıyorsa (ve isteğe bağlı olarak Adım 4), dağıtım hazırlığı perspektifinden P1-B **Go** kabul edilir.

Sonraki (isteğe bağlı): tek sayfalık bir kapanış raporu şablonunu standartlaştırın (“kanıt kontrol listesi + çıktılar + zaman damgaları”).

---

## Kanıt Çıktı Şablonu (Denetim İzi)

> Amaç: gizli bilgileri sızdırmadan kompakt, yeniden üretilebilir bir kanıt izi sağlamak.
> Çıktıları bu yapıda yapıştırın. Yukarıdaki kurallara göre kimlik bilgilerini ve hassas host’ları maskeleyin.

### Metadata
- Tarih (UTC): 2025-__-__T__ :__ :__Z
- Ortam: staging | prod | ci
- Servis sürümü: $(curl -sS http://localhost:8001/api/version | head -c 200)
- Git SHA (varsa): ________
- Runner/Host (maskeli): ________
- Operatör: ________ (isteğe bağlı)

---

### Adım 1 — Harici Migrasyon Geçidi (Postgres)

**Komut**```bash
cd /app/backend
export ENV=staging
export CI_STRICT=1
export DATABASE_URL='postgresql+asyncpg://user:***@host:5432/db'
export REDIS_URL='redis://:***@host:6379/0'

alembic upgrade head
echo "EXIT_CODE=$?"
alembic current
echo "EXIT_CODE=$?"
```**Çıkış Kodları**
- alembic upgrade head: EXIT_CODE=0|non-0
- alembic current: EXIT_CODE=0|non-0

**Çıktı (ilk/son satırlar)**
- upgrade head (ilk 10 satır):
  - ...
- upgrade head (son 10 satır):
  - ...
- current:
  - ...

---

### Adım 2 — Runtime Ready Geçidi (DB + Redis)

**Komut**```bash
curl -sS -i http://localhost:8001/api/ready
echo "EXIT_CODE=$?"
curl -sS -i http://localhost:8001/api/version
echo "EXIT_CODE=$?"
```**Beklenen**
- /api/ready: HTTP 200
- Yanıt, dependencies.database=connected, dependencies.redis=connected içerir
- Varsa: dependencies.migrations=head (veya eşdeğeri)

**Çıktı (tam)**
- /api/ready:
  - ...
- /api/version:
  - ...

---

### Adım 3 — Negatif Kanıt (Redis bozuk => Ready 503)

**Komut**```bash
export REDIS_URL='redis://:***@127.0.0.1:1/0'
# restart service if required by your runtime
curl -sS -i http://localhost:8001/api/ready
echo "EXIT_CODE=$?"
```**Beklenen**
- /api/ready: HTTP 503
- dependencies.redis=unreachable (veya eşdeğeri)

**Çıktı (tam)**
- /api/ready:
  - ...

---

### İsteğe Bağlı Adım 4 — Fail-fast (strict mod, listener yok)

**Komut**```bash
cd /app/backend
export CI_STRICT=1
unset REDIS_URL
pytest -q backend/tests/test_runtime_failfast_redis_uvicorn.py
echo "EXIT_CODE=$?"
```**Beklenen**
- EXIT_CODE=0

**Çıktı**
- ...

---

## Uygulama Notları (küçük ama değerli)
- “Servis sürümü” alanını her zaman doldurun — “bu kanıtı hangi build üretti?” sorusunu uçtan uca kapatır.
- Adım 2’de `dependencies.migrations` alanını belirtmek, runtime’da migrasyon sapmasını yakalamaya yardımcı olur.
- Bu şablon artifact-dostudur: gizli bilgiler olmadan bir CI artifact’i olarak saklayabilirsiniz.