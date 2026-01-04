# Log Şeması Sözleşmesi (P4.2)

Bu doküman, backend tarafından üretilen **kanonik, kararlı JSON log alanlarını** tanımlar.

**Hedef:** ops/uyarı/olay müdahalesi için belirsizliği ortadan kaldırmak.

Kapsam:
- `LOG_FORMAT=json` iken backend yapılandırılmış loglarına uygulanır.
- Ek alanlara izin verilir, ancak kanonik alanları **BOZMAMALI** veya yeniden adlandırmamalıdır.

---

## 1) Kanonik alanlar (zorunlu)

| Alan | Tür | Zorunlu | Notlar |
|---|---|---:|---|
| `timestamp` | string | evet | ISO-8601 UTC, ör. `2025-12-18T20:07:55.180000+00:00` |
| `level` | string | evet | `INFO`/`WARNING`/`ERROR` |
| `message` | string | evet | İnsan tarafından okunabilir mesaj |
| `service` | string | evet | ör. `backend` |
| `env` | string | evet | `local`/`dev`/`staging`/`prod` |

Notlar:
- `service` ve `env` mevcut olduğunda dahil edilir; `event=service.boot` üzerinde MUTLAKA bulunmalıdır.

---

## 2) Olay alanları (isteğe bağlı ama önerilir)

| Alan | Tür | Zorunlu | Notlar |
|---|---|---:|---|
| `event` | string | hayır | Filtreleme/uyarı için kararlı olay adı. Örnek: `service.boot`, `request` |

### Standart olay adları
- `service.boot` — uygulama başlangıcında yayımlanır (bkz. `server.py` startup hook)
- `request` — RequestLoggingMiddleware tarafından HTTP isteği başına yayımlanır

---

## 3) İstek korelasyonu ve çok kiracılılık

| Alan | Tür | Zorunlu | Notlar |
|---|---|---:|---|
| `request_id` | string | hayır | FE hataları ve BE loglarını ilişkilendirir. `X-Request-ID` değerini yansıtır |
| `tenant_id` | string | hayır | Kiracı bağlamı. Mevcut olduğunda `X-Tenant-ID` header’ını yansıtır |

---

## 4) HTTP istek metrikleri (`event=request` iken)

| Alan | Tür | Zorunlu | Notlar |
|---|---|---:|---|
| `method` | string | hayır | `GET`, `POST`, ... |
| `path` | string | hayır | Yalnızca URL path (host/query yok), ör. `/api/version` |
| `status_code` | number | hayır | HTTP durum kodu |
| `duration_ms` | number | hayır | ms cinsinden istek gecikmesi |

---

## 5) Güvenlik / gizlilik (uyulması zorunlu)

### 5.1 Maskeleme kuralları
Ham kimlik bilgilerini loglamayın.

Şunlarla eşleşen (büyük/küçük harfe duyarsız) yapılandırılmış payload anahtarları maskelenir:
- `authorization`, `cookie`, `set-cookie`, `token`, `secret`, `api_key`

(Uygulama referansı: `backend/app/core/logging_config.py`.)

### 5.2 Kimlik alanları
Zaten güvenliyse/hash’lenmişse log ekstralarında bulunabilir:
- `user_id` (string)
- `actor_user_id` (string)
- `ip` (string)

İleride eklerseniz, tercih edin:
- hash’lenmiş tanımlayıcılar (bkz. security utils)
- güvenlik incelemeleri için gerekmedikçe tam IP saklamaktan kaçının

---

## 6) Build metadatası (`event=service.boot` üzerinde zorunlu)

Servis boot ettiğinde, şunları loglayın:
- `event=service.boot`
- `version`, `git_sha`, `build_time`

Şuna yanıt vermek için kullanılır: **"Hangi sürüm çalışıyor?"**

---

## 7) Uyarı eşlemesi (P3.3 hizalaması)

Bu sözleşme `docs/ops/alerts.md` dokümanını destekler:
- **5xx oranı**: `event=request` ile filtreleyin ve `status_code >= 500` değerini `path` başına agregasyonlayın
- **gecikme**: `duration_ms` (p95) değerini `path` başına agregasyonlayın
- **istek korelasyonu**: `request_id` kullanın

Güvenlik/denetim temelli uyarılar mümkün olduğunda **denetim olaylarını** (DB destekli) kullanmalı, triyaj için logları kullanmalıdır.

---

## 8) Uyumluluk garantisi

- (1), (3) bölümlerindeki kanonik alanlar ve istek metrikleri (4) yeniden adlandırılmamalıdır.
- Yeni alanlar ekstra olarak eklenebilir.
- Alanların kaldırılması bir sürüm notu ve ops onayı gerektirir.