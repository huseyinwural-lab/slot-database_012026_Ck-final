# Logs (TR)

**Menü yolu (UI):** System → Logs  
**Frontend route:** `/system/logs`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Önce incident kategorisini belirle: **errors**, **deployments**, **db**, **cache**, **queues** veya genel **events**.
- Mutlaka bir **time window** al ve mümkünse **request path** (ve varsa `x-request-id`) ile korele et.
- Değişiklik yapıldıysa, UI etkisini doğrula ve kanıtı **Audit Log**’da ara.
- UI kategorisi boşsa, backend endpoint’inin stub olabileceğini düşün (gap’e bak) ve container log’a pivot et.

---

## 1) Amaç ve kapsam

System Logs, sistem event kayıtlarını ve operasyon kategorilerini (cron, deployments, config changes, error logs, queue/workers, DB/cache, archive) admin UI üzerinden göstermeyi hedefler. İlk müdahale triage, korelasyon ve kanıt toplama için kullanılır.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin) / Ops
- Incident sırasında Support & Engineering (verildiyse)

---

## 3) Alt başlıklar / kategoriler

Mevcut UI (`frontend/src/pages/SystemLogs.jsx`) kategorileri endpoint’lere map eder:
- System Events → `GET /api/v1/logs/events`
- Cron Jobs → `GET /api/v1/logs/cron`
- Service Health → `GET /api/v1/logs/health`
- Deployments → `GET /api/v1/logs/deployments`
- Config Changes → `GET /api/v1/logs/config`
- Error Logs → `GET /api/v1/logs/errors`
- Queue / Workers → `GET /api/v1/logs/queues`
- Database Logs → `GET /api/v1/logs/db`
- Cache Logs → `GET /api/v1/logs/cache`
- Log Archive → `GET /api/v1/logs/archive`

---

## 4) Temel akışlar (adım adım)

### 4.1 Incident triage
1) Logs aç.
2) Önce **Error Logs** ve **System Events** bak.
3) Semptoma göre kategoriye derinleş:
   - Deployment regression → Deployments
   - Slow query/timeout → DB
   - Stale config → Cache / Config Changes

### 4.2 Escalation paketi hazırlama
1) Timestamp aralığını kaydet.
2) Log satırı JSON’ını kopyala.
3) DevTools’tan etkilenen endpoint + status code’u al.
4) Tenant context’i ekle (varsa).

---

## 5) Saha rehberi (pratik ipuçları)

- Logs “ne oldu?”yu, Audit Log “kim neyi değiştirdi?”yi anlatır.
- Kategori boşsa endpoint stub olabilir.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** “No logs found for this category.”
   - **Muhtemel neden:** aralıkta event yok veya endpoint boş liste döndürüyor.
   - **Çözüm:** System Events’e dön; zaman aralığını genişlet; backend davranışını doğrula.
   - **Doğrulama:** `GET /api/v1/logs/<category>` satır döner.

2) **Semptom:** Logs yükleniyor ama alanlar garip/eksik.
   - **Muhtemel neden:** kategori bazında schema tutarsız.
   - **Çözüm:** raw JSON ve timestamp ile ilerle; schema standardizasyonu için escalate.
   - **Doğrulama:** event key’leri tutarlı hale gelir.

3) **Semptom:** Incident var ama Error Logs boş.
   - **Muhtemel neden:** error ingestion bu kategoriye bağlı değil.
   - **Çözüm:** container log’a pivot.
   - **Doğrulama:** container log stack trace/timeout içerir.

4) **Semptom:** Logs ekranı yavaş.
   - **Muhtemel neden:** büyük payload / tablo render.
   - **Çözüm:** refresh; daha dar time window; derin analiz için container log.
   - **Doğrulama:** yüklenme süresi düşer.

5) **Semptom:** Logs endpoint’lerinde 403 Forbidden.
   - **Muhtemel neden:** platform owner değil.
   - **Çözüm:** owner admin kullan.
   - **Doğrulama:** endpoint 200.

6) **Semptom:** Cron sekmesi aksiyonlanabilir bilgi vermiyor.
   - **Muhtemel neden:** cron endpoint stub.
   - **Çözüm:** worker/job runner log’larını kontrol et.
   - **Doğrulama:** cron job event üretir.

7) **Semptom:** Deployments sekmesi son deploy’u göstermiyor.
   - **Muhtemel neden:** deployments endpoint stub.
   - **Çözüm:** deployment sistem log’larına bak.
   - **Doğrulama:** deployment kaydı görünür.

8) **Semptom:** DB/Cache sekmeleri issue ile korele değil.
   - **Muhtemel neden:** endpoint stub veya wiring yok.
   - **Çözüm:** infra monitoring + container log kullan.
   - **Doğrulama:** DB/cache event’leri gözlenir.

9) **Semptom:** Trace View “Coming Soon”.
   - **Muhtemel neden:** feature implement edilmemiş.
   - **Çözüm:** request_id ile log korelasyonu.
   - **Doğrulama:** (gelecek) tracing UI.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Semptom:** Çoğu kategori boş liste döndürüyor.
   - **Likely Cause:** backend `routes/logs.py` `/events` dışında birçok kategoride `[]` döndürüyor.
   - **Impact:** Admin kategori sekmelerine güvenemez; derin incident’te container log gerekir.
   - **Admin Workaround:**
     - Birincil: **System Events** sekmesi.
     - Cron/deployments/db/cache için container log.
   - **Escalation Package:**
     - HTTP method + path: `GET /api/v1/logs/<category>` (cron/health/deployments/config/errors/queues/db/cache/archive)
     - Expected vs actual: expected event; actual `[]`
     - Log keyword: `logs/<category>`
   - **Resolution Owner:** Backend
   - **Verification:** Event varsa her kategori endpoint’i non-empty döner.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Sekme değişince dataset değişir.

### 8.2 System → Audit Log
- Config change gibi aksiyonlarda audit event var mı bak.

### 8.3 Container/app log
- Request path + timeframe ile ara.

### 8.4 DB audit (varsa)
- `auditlog` / `auditevent` incident ile uyumlu olmalı.

---

## 9) Güvenlik notları + geri dönüş

- Log’lar hassas veri içerebilir; erişimi kısıtlayın.

---

## 10) İlgili linkler

- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
