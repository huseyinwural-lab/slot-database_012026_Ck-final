# Audit Log (TR)

**Menü yolu (UI):** System → Audit Log  
**Frontend route:** `/audit`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Riskli bir değişiklik olduysa: önce **kim** (actor_user_id) ve **ne** (action + resource_id) bilgisini çıkar.
- **request_id** ile audit event → container log korelasyonu yap.
- Kanıtı (CSV export) incident ticket/post-mortem’e ekle.
- Beklenen event yoksa: time range’i ve bu aksiyonun audit edilip edilmediğini kontrol et.

---

## 1) Amaç ve kapsam

Audit Log, admin aksiyonlarının değiştirilemez, sorgulanabilir kaydıdır. Compliance kanıtı, incident forensics ve operasyonel sorumluluk için kullanılır.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner / Security / Compliance
- Incident sırasında Engineering

---

## 3) Alt başlıklar / fonksiyon alanları

Mevcut UI (`frontend/src/pages/AuditLog.jsx`):
- Filtreler (action, resource_type, status, actor_id, request_id, time range)
- Tablo görünümü
- Export CSV
- Event detay dialog (diff/before-after/raw)

**API çağrıları (frontend’den gözlemlendi):**
- Liste: `GET /api/v1/audit/events?since_hours=<n>&limit=<n>&action=<...>&resource_type=<...>&status=<...>&actor_user_id=<...>&request_id=<...>`
- Export: `GET /api/v1/audit/export?since_hours=<n>`

Backend: `backend/app/routes/audit.py`

---

## 4) Temel akışlar (adım adım)

### 4.1 Şüpheli değişikliği inceleme
1) Time range seç (başlangıç: Last 24 Hours).
2) **action** (biliyorsan) veya **resource_type** ile filtrele.
3) Event detayını aç.
4) `request_id` kopyala ve backend log’la korele et.

### 4.2 Compliance kanıtı üretme
1) Filtreleri uygula (time range + actor).
2) **Export CSV**.
3) CSV’yi ticket/post-mortem’e ekle.

---

## 5) Saha rehberi (pratik ipuçları)

- request_id varsa en iyi filtre budur.
- “Before/After” ve “Diff” hızlı inceleme sağlar.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** Audit event listesi boş.
   - **Muhtemel neden:** time range dar; event yok.
   - **Çözüm:** since_hours artır; filtreleri kaldır.
   - **Doğrulama:** liste endpoint’i item döner.

2) **Semptom:** Beklenen event yok.
   - **Muhtemel neden:** bu build’de aksiyon audit edilmiyor.
   - **Çözüm:** kanıt için container log kullan; audit eklenmesi için escalate.
   - **Doğrulama:** implementasyon sonrası aksiyon audit event üretir.

3) **Semptom:** Export fail.
   - **Muhtemel neden:** backend export route hata veya auth.
   - **Çözüm:** `GET /api/v1/audit/export` response kontrol; daha küçük time range dene.
   - **Doğrulama:** CSV iner.

4) **Semptom:** Diff boş.
   - **Muhtemel neden:** diff_json üretilmemiş.
   - **Çözüm:** raw JSON ve before/after kullan.
   - **Doğrulama:** raw JSON detay içerir.

5) **Semptom:** 403 Forbidden.
   - **Muhtemel neden:** platform owner değil.
   - **Çözüm:** owner admin ile dene.
   - **Doğrulama:** endpoint 200.

6) **Semptom:** request_id yok.
   - **Muhtemel neden:** legacy event.
   - **Çözüm:** timestamp + actor ile korele et.
   - **Doğrulama:** container log timeframe ile eşleşir.

7) **Semptom:** DENIED event’ler görünüyor.
   - **Muhtemel neden:** policy request’i blokladı.
   - **Çözüm:** permissions ve tenant context doğrula; onaysız bypass yapma.
   - **Doğrulama:** doğru role ile sonraki request başarılı.

8) **Semptom:** Çok gürültü.
   - **Muhtemel neden:** filtreler geniş.
   - **Çözüm:** action/resource_type/actor ile daralt.
   - **Doğrulama:** ilgili subset görünür.

9) **Semptom:** Timestamp/timezone karışıyor.
   - **Muhtemel neden:** UI timestamp’i locale’e çeviriyor.
   - **Çözüm:** raw JSON’daki ISO timestamp’i esas al.
   - **Doğrulama:** sıralama/yorum tutarlı.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Export CSV hata veriyor veya boş dosya indiriyor.
   - **Likely Cause:** export route var ama tenant scope / filtre beklenmedik şekilde çalışıyor olabilir.
   - **Impact:** Kanıt üretimi bloklanır.
   - **Admin Workaround:** Daha küçük time range export; geçici olarak event detail screenshot’ı ile kanıt.
   - **Escalation Package:**
     - HTTP method + path: `GET /api/v1/audit/export`
     - Request sample: `since_hours=<n>`
     - Expected vs actual: expected CSV; actual error/empty
     - Log keyword: `audit export`, `since_hours`
   - **Resolution Owner:** Backend
   - **Verification:** export doğru event count ile CSV indirir.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Filtreler çalışır; liste güncellenir.

### 8.2 System → Logs
- request_id ile audit → runtime log korelasyonu.

### 8.3 Container/app log
- `request_id`, `action`, `resource_id` ile ara.

### 8.4 DB audit (varsa)
- Kanonik tablo: `auditevent`.

---

## 9) Güvenlik notları + geri dönüş

- Audit log kanıttır; değiştirilemez.

---

## 10) İlgili linkler

- Logs: `/docs/new/tr/admin/system/logs.md`
- Break-glass: `/docs/new/tr/runbooks/break-glass.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
