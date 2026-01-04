# VIP Games (TR)

**Menü yolu (UI):** Core → VIP Games  
**Frontend route:** `/vip-games`  
**Sadece owner:** Hayır  

---

## Ops Checklist (read first)

- Doğru **tenant context** üzerinde olduğunuzu doğrulayın.
- Incident yönünü belirleyin:
  - “VIP oyun normal kullanıcıda görünüyor” → VIP görünürlüğünü kaldır / rollback mapping.
  - “VIP kullanıcı VIP oyunu göremiyor” → VIP işaretini ve propagasyonu kontrol et.
- Değişikliği **UI (VIP Games + Games)** ve **System → Audit Log** üzerinden doğrulayın.
- Yansıma yoksa **System → Logs** ve container log’larda `games` / `vip` / `tags` arayın.

---

## 1) Amaç ve kapsam

VIP Games, yüksek değerli oyuncular için VIP-only (veya VIP-highlight) oyun kataloğunu yönetir. Bu build’de VIP üyeliği, oyun kaydına uygulanan **tag** (`VIP`) ile temsil edilir.

---

## 2) Kim kullanır / yetki gereksinimi

- Tenant Admin / Ops: VIP katalog yönetimi.
- Platform Owner: tenant context ile tenant’lar arası operasyon.

---

## 3) VIP görünürlük kriterleri (VIP nasıl belirlenir?)

Mevcut implementasyon (`frontend/src/pages/VipGames.jsx`):
- Oyun VIP kabul edilir: `game.tags` içinde `VIP` varsa.

Operasyonel not:
- Bu mekanizma **katalog-side metadata**’dır; player segment engine değildir.
- Segment/tier bazlı enforcement gerekiyorsa player lobby tarafında ayrıca enforce edilmelidir.

---

## 4) Temel akışlar (adım adım)

### 4.1 VIP oyunları görüntüleme
1) VIP Games aç.
2) Sayfa tüm oyunları çeker ve `tags.includes('VIP')` ile filtreler.

**API çağrıları (frontend’den gözlemlendi):**
- Oyun listesi: `GET /api/v1/games` (UI array veya paginated kabul ediyor)

### 4.2 Oyunu VIP yapma
1) **Add VIP Game** tıkla.
2) Oyun ara.
3) **Add** tıkla.

**API çağrıları (frontend’den gözlemlendi):**
- Tag update: `PUT /api/v1/games/{game_id}/details` body `{ tags: [ ... , "VIP" ] }`

### 4.3 VIP’den çıkarma
1) VIP listesinde remove (trash) tıkla.

**API çağrıları:**
- Tag update: `PUT /api/v1/games/{game_id}/details` body `{ tags: <VIP hariç> }`

### 4.4 Propagation / caching notu
- Player lobby katalog cache’liyorsa yansıma gecikmesi olur.
- Değişiklik sonrası test hesapla doğrula.

---

## 5) Saha rehberi (pratik ipuçları)

- VIP görünürlük değişiklikleri gelir ve UX’i etkiler.
- Incident sırasında tek tek değiştir.
- Incident notu tut: ne değişti, neden, rollback planı.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** VIP oyun normal kullanıcıda görünüyor.
   - **Muhtemel neden:** VIP tag var ama player-side enforcement/segment gating yok.
   - **Çözüm:** `VIP` tag’ini kaldır (geçici containment) ve lobby kurallarını doğrula.
   - **Doğrulama:** VIP olmayan test hesap oyunu göremez.

2) **Semptom:** VIP kullanıcı VIP oyunu göremiyor.
   - **Muhtemel neden:** VIP tag uygulanmamış; cache gecikmesi; tenant context yanlış.
   - **Çözüm:** Oyunda `VIP` tag var mı doğrula; cache/TTL bekle veya refresh; tenant context doğrula.
   - **Doğrulama:** VIP kullanıcı refresh sonrası oyunu görür.

3) **Semptom:** Add/Remove sırasında “Failed to update status” toast.
   - **Muhtemel neden:** backend endpoint yok veya validation error.
   - **Çözüm:** DevTools’ta fail eden request ve payload’ı al; bir kez retry.
   - **Doğrulama:** `PUT /api/v1/games/{id}/details` 200 döner.

4) **Semptom:** VIP Games listesi boş ama VIP bekleniyor.
   - **Muhtemel neden:** `GET /api/v1/games` empty; tenant yanlış; API fail.
   - **Çözüm:** Games ekranını kontrol et; tenant doğrula; Network’e bak.
   - **Doğrulama:** games listesi dolu ve VIP filtre item döner.

5) **Semptom:** Oyun iki kez görünüyor veya VIP filtre tutarsız.
   - **Muhtemel neden:** duplicate katalog kaydı veya ID tutarsızlığı.
   - **Çözüm:** Games ekranında duplicate’leri bul; disable et.
   - **Doğrulama:** tek canonical kayıt kalır.

6) **Semptom:** VIP tag kaldırıldı ama normal kullanıcı hâlâ görüyor.
   - **Muhtemel neden:** lobby cache yenilenmedi.
   - **Çözüm:** cache invalidate (varsa) veya TTL bekle; tekrar test.
   - **Doğrulama:** TTL/refresh sonrası oyun kaybolur.

7) **Semptom:** VIP tag eklendi ama VIP kullanıcı hâlâ görmüyor.
   - **Muhtemel neden:** player VIP cohort/tier değil; lobby gating farklı.
   - **Çözüm:** player VIP statüsünü doğrula; enforcement logic doğrula.
   - **Doğrulama:** doğru VIP hesap oyunu görür.

8) **Semptom:** VIP update isteği 404 Not Found.
   - **Muhtemel neden:** backend `PUT /api/v1/games/{id}/details` route’u yok.
   - **Çözüm:** No admin-side workaround.
   - **Doğrulama:** backend fix sonrası endpoint 200.

9) **Semptom:** `VIP` tag değişiklikleri geri dönüyor.
   - **Muhtemel neden:** başka bir sistem tag’leri overwrite ediyor (import sync/provider sync).
   - **Çözüm:** ilgili sync job’u pause et (varsa); engineering ile koordine et.
   - **Doğrulama:** refresh sonrası tag stabil kalır.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Add/Remove VIP 404 ile fail.
   - **Likely Cause:** UI `PUT /api/v1/games/{game_id}/details` çağırıyor; backend route yok veya deploy edilmemiş.
   - **Impact:** VIP katalog yönetimi bloklanır.
   - **Admin Workaround:** No admin-side workaround.
   - **Escalation Package:**
     - HTTP method + path: `PUT /api/v1/games/{game_id}/details`
     - Request sample: `{ "tags": ["VIP", "..."] }`
     - Expected vs actual: expected 200; actual 404
     - Log keyword’leri:
       - `games`
       - `details`
       - `404`
   - **Resolution Owner:** Backend
   - **Verification:** Fix sonrası tag update başarılı; refresh sonrası VIP listesi güncel.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Add/Remove sonrası VIP listesi güncellenir.
- Games ekranında tags/status tutarlı.

### 8.2 System → Audit Log
- Katalog mutation event’leri (isim değişebilir): `game.updated`, `visibility.changed`.

### 8.3 System → Logs
- Games endpoint’leri etrafında error/timeout var mı bak.

### 8.4 Container/app log
- Arama anahtar kelimeleri:
  - `games`
  - `vip`
  - `tags`
  - `/games/<id>/details`

### 8.5 DB audit (varsa)
- Doğru tenant için game tags doğrula.
- `auditevent` ile audit trail doğrula.

---

## 9) Güvenlik notları + geri dönüş

- VIP yanlış konfigürasyon premium içeriği sızdırabilir veya VIP kullanıcıyı engeller.

Rollback (önerilen):
1) Geçici containment: VIP tag’ini kaldır veya oyunu disable et.
2) Lobby enforcement logic doğrula.
3) Doğrulama sonrası VIP tag’i geri ekle.

---

## 10) İlgili linkler

- Games: `/docs/new/tr/admin/core/games.md`
- Feature Flags: `/docs/new/tr/admin/system/feature-flags.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
