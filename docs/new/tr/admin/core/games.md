# Games (TR)

**Menü yolu (UI):** Core → Games  
**Frontend route:** `/games`  
**Sadece owner:** Hayır  

---

## 1) Amaç ve kapsam

Games menüsü, tenant’ın oyun kataloğu için operasyonel kontrol düzlemidir: oyunları listeleme, görünürlüğü enable/disable yönetimi, live table yönetimi ve katalog ingest/import akışları.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin): doğru tenant context seçerek tenant’lar arası operasyon yapabilir.
- Tenant Admin / Ops: günlük katalog operasyonu (enable/disable, görünürlük doğrulama).
- Risk/Compliance: incident anlarında görünürlük/segment doğrulaması yapabilir.

---

## 3) Alt başlıklar / sekmeler

Mevcut UI’da (`frontend/src/pages/GameManagement.jsx`):
- **Slots & Games**
- **Live Tables**
- **Upload & Import**

---

## 4) Temel akışlar (adım adım)

### 4.1 Oyun arama/filtreleme (Slots & Games)
1) **Slots & Games** sekmesini aç.
2) **Category filter** kullan (örn. Slot, Crash, Dice, Table Poker, Table Blackjack).
3) (Varsa) provider/supplier filtrelerini kullan.

**API çağrıları (frontend’den gözlemlendi):**
- Oyun listesi: `GET /api/v1/games?category=<...>&page=<n>&page_size=<n>`

### 4.2 Oyun enable/disable
1) **Slots & Games** listesinden oyunun toggle’ını değiştir.
2) Listeyi yenileyip status’un güncellendiğini doğrula.

**API çağrıları (frontend’den gözlemlendi):**
- Toggle: `POST /api/v1/games/{game_id}/toggle`

### 4.3 Live tables (create + doğrulama)
1) **Live Tables** sekmesine geç.
2) **Create Table** aksiyonunu seç.
3) Gerekli alanları doldur (name/provider/min bet/max bet).
4) Kaydet ve listede göründüğünü doğrula.

**API çağrıları (frontend’den gözlemlendi):**
- Table listesi: `GET /api/v1/tables`
- Table oluşturma: `POST /api/v1/tables`

### 4.4 Upload & Import (manual bundle)

UI, “manual upload + preview + import confirm” akışını destekler.

1) **Upload & Import** sekmesini seç.
2) File-based method seç.
3) JSON/ZIP bundle ve opsiyonel metadata yükle (source_label, notes, client_type, launch_url, min_version).
4) Preview item’lar ve errors/warnings incele.
5) **Import** ile finalize et.

**API çağrıları (frontend’den gözlemlendi):**
- Manual upload/analyze: `POST /api/v1/game-import/manual/upload` (multipart)
- Job preview: `GET /api/v1/game-import/jobs/{job_id}`
- Import confirm: `POST /api/v1/game-import/jobs/{job_id}/import`

**Önemli implementasyon notu:** Mevcut backend route’larında `/api/v1/game-import` stub durumda ve “manual/*” endpoint’leri bulunmuyor. Bu build’de UI bu endpoint’ler için **404 Not Found** alabilir.

---

## 5) Saha rehberi (pratik ipuçları)

- Enable/disable öncesi mutlaka **tenant context** doğrula.
- Değişiklikleri düşük trafik zamanlarında yap.
- Toggle/import sonrası, player/lobby tarafında cache varsa “yansıma gecikmesi” beklenebilir.
- VIP görünürlük kuralları için VIP yapılandırmasıyla doğrulama yap.

**Yapmayın:**
- Rollback planı olmadan büyük batch enable.
- Required alanlar/unique key doğrulanmadan katalog import.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

> Incident hazırlığı için minimum set (8+).

1) **Semptom:** Oyun listede görünmüyor.
   - **Muhtemel neden:** Category filter dışlıyor; yanlış tenant context.
   - **Çözüm:** Category filter’ı **All** yap; tenant context’i doğrula.
   - **Doğrulama:** Liste yenilenince oyun görünür; `GET /api/v1/games` 200 döner.

2) **Semptom:** Toggle çalışmış gibi görünüyor ama listede eski status var.
   - **Muhtemel neden:** UI refresh olmadı; toggle isteği fail.
   - **Çözüm:** Refresh et; `POST /api/v1/games/{id}/toggle` response’u kontrol et.
   - **Doğrulama:** Refresh sonrası status değişir ve `GET /api/v1/games` bunu yansıtır.

3) **Semptom:** Oyun enable ama player tarafında görünmüyor.
   - **Muhtemel neden:** Player cache; feature gating; tenant-lobby mapping.
   - **Çözüm:** Cache temizle (uygunsa); feature flag’leri doğrula; tenant mapping kontrol et.
   - **Doğrulama:** Player lobby listesi oyunu içerir; log’larda “blocked” yok.

4) **Semptom:** Launch’ta siyah ekran / provider error.
   - **Muhtemel neden:** Provider credential/config eksik; provider outage; launch URL mismatch.
   - **Çözüm:** Provider config + API key doğrula; provider status kontrol et.
   - **Doğrulama:** Backend log’larında başarılı launch/session; provider error yok.

5) **Semptom:** Live table create sonrası listede görünmüyor.
   - **Muhtemel neden:** `POST /api/v1/tables` validasyon hatası.
   - **Çözüm:** Required alanlar ve numeric aralıkları doğrula; yeniden dene.
   - **Doğrulama:** `GET /api/v1/tables` yeni kaydı içerir.

6) **Semptom:** Upload & Import 404 Not Found.
   - **Muhtemel neden:** Backend endpoint’ler implement edilmemiş (`/api/v1/game-import/manual/*`).
   - **Çözüm:** Backend release route’ları doğrula; yoksa supported import path kullan veya ertele.
   - **Doğrulama:** `POST /api/v1/game-import/manual/upload` 200 + job id döner.

7) **Semptom:** Import “validation failed”.
   - **Muhtemel neden:** Required field eksik; invalid enum; bundle bozuk.
   - **Çözüm:** Bundle format/alanları düzelt; yeniden yükle.
   - **Doğrulama:** Preview `total_errors=0` ve item listesi dolu.

8) **Semptom:** Import duplicate kayıt üretti.
   - **Muhtemel neden:** Unique key/idempotency stratejisi yok; provider ID çakışması.
   - **Çözüm:** Unique identifier zorunlu kıl; dataset’i düzeltip yeniden çalıştır.
   - **Doğrulama:** Her unique id için tek kayıt.

9) **Semptom:** VIP oyun normal kullanıcıya açıldı.
   - **Muhtemel neden:** Segment/visibility mapping yanlış.
   - **Çözüm:** VIP kural ve segment targeting doğrula; yanlış mapping’i geri al.
   - **Doğrulama:** VIP dışı test hesap oyunu göremez.

---

## 7) Çözüm adımları (adım adım)

1) DevTools (Network) ile kanıt topla: failing path + status + payload.
2) Tenant context doğrula.
3) Aksiyonu bir kez tekrar çalıştır, sonra refresh.
4) Backend log’larında timeframe + endpoint path ile ara.
5) Player etkisi varsa player tarafında doğrula.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Games listesinde enabled/disabled state doğru görünür.
- Live Tables listesi oluşturulan kayıtları içerir.
- Upload & Import preview status ve item’lar görünür.

### 8.2 System → Logs
- Oyun toggle/import etrafındaki runtime error/timeout’lara bak.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `games` / `toggle`
  - `tables`
  - `game-import` / `import`
  - provider adı / provider error code

### 8.4 System → Audit Log
- Eğer katalog operasyonları audit ediliyorsa, timeframe + resource id ile filtrele.
- Muhtemel action isimleri (implementasyona göre): `game.updated`, `game.imported`, `table.created`, `visibility.changed`.

### 8.5 DB audit (varsa)
- Tenant-scoped kayıtların `tenant_id` alanı doğru tenant ile eşleşmeli.
- Yanlış tenant şüphesinde `tenant_id` doğrulaması yap.

---

## 9) Güvenlik notları + geri dönüş

- Katalog görünürlük değişiklikleri gelir ve player deneyimini doğrudan etkiler.

Rollback (önerilen):
1) Etkilenen oyunu/oyunları disable et.
2) Mapping/segment değişikliklerini geri al.
3) Player görünürlüğünü tekrar test et.

---

## 10) İlgili linkler

- VIP görünürlük: `/docs/new/tr/admin/core/vip-games.md`
- Tenant context güvenliği: `/docs/new/tr/admin/system/tenants.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
