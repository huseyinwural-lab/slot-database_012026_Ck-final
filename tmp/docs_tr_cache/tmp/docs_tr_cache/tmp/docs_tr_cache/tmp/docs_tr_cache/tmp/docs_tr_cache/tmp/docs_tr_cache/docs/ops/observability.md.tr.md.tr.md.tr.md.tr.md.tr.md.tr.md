# Gözlemlenebilirlik (P2)

## 1) İstek Korelasyonu (X-Request-ID)
- Backend, gelen `X-Request-ID` değerini **yalnızca** şu koşulu sağlıyorsa kabul eder:
  - `^[A-Za-z0-9._-]{8,64}$`
- Eksik/geçersizse, backend bir UUID üretir.
- Backend, seçilen değeri **yanıt başlığında** geri döner:
  - `X-Request-ID: <value>`

### Bu neden önemlidir
- Destek/hata ayıklama: bir kullanıcı, ilgili tüm logları bulmak için tek bir ID paylaşabilir.
- Varsayılan olarak güvenli: güvenilmeyen/aşırı büyük başlık değerlerini yok sayarız.

## 2) JSON Logları (prod/staging varsayılanı)
- `ENV=prod|staging` ⇒ JSON logları varsayılandır (`LOG_FORMAT=auto`).
- `ENV=dev|local` ⇒ insan tarafından okunabilir loglar varsayılandır.
- Geçersiz kılma her zaman mümkündür:
  - `LOG_FORMAT=json` veya `LOG_FORMAT=plain`

### Önerilen log alanları (Kibana/Grafana)
İndekslemek için stabil alanlar:
- `timestamp` (ISO, UTC)
- `level`
- `message`
- `event` (varsa)
- `request_id`
- `tenant_id`
- `method`
- `path`
- `status_code`
- `duration_ms`
- `client_ip` (varsa, ör. rate-limit olayları)

Örnek Kibana sorgu fikirleri:
- Tek bir isteği bul:
  - `request_id:"<id>"`
- Oran sınırlama olayları:
  - `event:"auth.login_rate_limited"`

## 3) Hassas Veri Maskeleme
JSON logger, yapılandırılmış payload’ların herhangi bir yerindeki anahtarları (büyük/küçük harfe duyarsız) redakte eder:
- `authorization`, `cookie`, `set-cookie`, `password`, `token`, `secret`, `api_key`

> Not: Bu, yapılandırılmış `extra={...}` payload’ları için geçerlidir. Serbest metin mesajına ham header’ları / token’ları loglamaktan kaçının.

## 4) Health ve Readiness
- **Liveness**: `GET /api/health`
  - Süreç ayakta
- **Readiness**: `GET /api/ready` (`/api/readiness` için takma ad)
  - DB bağlantı kontrolü (`SELECT 1`)
  - `alembic_version` üzerinden hafif migration durum kontrolü

Docker Compose’da backend container healthcheck hedefi `/api/ready`’dir.