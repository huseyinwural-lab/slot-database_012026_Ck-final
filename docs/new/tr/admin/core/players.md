# Players (TR)

**Menü yolu (UI):** Core → Players  
**Frontend route:** `/players`  
**Sadece owner:** Hayır  

---

## 1) Amaç ve kapsam

Players menüsü, seçili tenant içindeki oyuncu hesaplarını arama, inceleme ve yönetme için ana operasyon alanıdır. İnceleme (risk/support), operasyonel aksiyonlar (status değişimi) ve player-level detaylara navigasyon sağlar.

---

## 2) Kim kullanır / yetki gereksinimi

- Tenant Admin / Ops: günlük oyuncu yönetimi.
- Support: oyuncu vaka çözümü (login sorunları, kısıtlar, dispute).
- Risk: şüpheli aktivite inceleme ve kısıt uygulama.
- Platform Owner: tenant context ile tenant’lar arası görünürlük.

---

## 3) Alt başlıklar / ekranlar

Mevcut UI:
- Player list (`frontend/src/pages/PlayerList.jsx`)
- Player detail (`frontend/src/pages/PlayerDetail.jsx`)

---

## 4) Temel akışlar (adım adım)

### 4.1 Arama ve filtre
1) Players aç.
2) **Search** alanını kullan (username/email).
3) **Status** filtresi seç (active/disabled/all).
4) (Gerekirse) **Include disabled** ile soft-disabled hesapları dahil et.

**API çağrıları (frontend’den gözlemlendi):**
- Liste: `GET /api/v1/players?search=<q>&status=<status>&page=<n>&page_size=<n>`

### 4.2 Player profiline gir
1) Listeden oyuncu satırına tıkla.
2) Profil alanlarını ve aktiviteyi incele.

**API çağrıları:**
- Detay: `GET /api/v1/players/{player_id}`

### 4.3 Player güncelleme (profil/status)
1) Player detail aç.
2) Değişikliği uygula (status, notlar, kısıtlar UI’a bağlı).

**API çağrıları (backend destekli):**
- Update: `PUT /api/v1/players/{player_id}`

### 4.4 Player disable (soft delete)
1) Player detail aç.
2) Disable aksiyonunu seç.
3) Onayla.

**API çağrıları (backend destekli):**
- Disable: `DELETE /api/v1/players/{player_id}` (soft disable)

---

## 5) Saha rehberi (pratik ipuçları)

- Kısıt uygulamadan önce tenant context doğrula.
- Containment için **soft disable** tercih et.
- Wallet uyuşmazlıklarında Finance ledger ile cross-check yap.

**Yapmayın:**
- Reason kaydı olmadan oyuncu disable.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

> Minimum set (9 madde).

1) **Semptom:** Oyuncu bulunamıyor.
   - **Muhtemel neden:** Arama terimi yanlış; tenant context yanlış.
   - **Çözüm:** Email ve username ile ara; tenant context doğrula.
   - **Doğrulama:** `GET /api/v1/players` beklenen sonucu döner.

2) **Semptom:** Oyuncu listesi boş.
   - **Muhtemel neden:** Filtre çok dar; status seçimi disabled oyuncuları gizliyor.
   - **Çözüm:** Status `all` yap; gerekiyorsa include_disabled aç.
   - **Doğrulama:** Liste endpoint’i items + meta döner.

3) **Semptom:** Oyuncuya tıklayınca 404 geliyor.
   - **Muhtemel neden:** Tenant boundary (oyuncu başka tenant’ta).
   - **Çözüm:** Tenant context doğrula; doğru tenant’ta ara.
   - **Doğrulama:** Doğru tenant’ta `GET /api/v1/players/{id}` 200 döner.

4) **Semptom:** Update 400 ile fail.
   - **Muhtemel neden:** Desteklenmeyen field veya invalid status.
   - **Çözüm:** Sadece desteklenen alanları güncelle; valid değerlerle tekrar dene.
   - **Doğrulama:** `PUT /api/v1/players/{id}` success.

5) **Semptom:** Disable 403 ile fail.
   - **Muhtemel neden:** Rol yetkisi yok.
   - **Çözüm:** Yetkili admin ile dene; permission hatasıysa escalate.
   - **Doğrulama:** Disable başarılı ve status `disabled`.

6) **Semptom:** Disable sonrası hâlâ aktif görünüyor.
   - **Muhtemel neden:** UI cache / refresh edilmedi.
   - **Çözüm:** Refresh; listeyi yeniden çek.
   - **Doğrulama:** `GET /api/v1/players` `status=disabled` gösterir.

7) **Semptom:** Değişiklik sonrası oyuncu login olamıyor.
   - **Muhtemel neden:** Status disabled veya ek kısıtlar.
   - **Çözüm:** Status ve kısıtları kontrol et; yanlışsa geri al.
   - **Doğrulama:** Login başarılı; log’larda auth error yok.

8) **Semptom:** Segment/etiket görünmüyor.
   - **Muhtemel neden:** Feature kapalı veya veri yüklenemiyor.
   - **Çözüm:** Entitlement kontrol; refresh; segment servisi down ise escalate.
   - **Doğrulama:** UI segmentleri gösterir; log’larda error yok.

9) **Semptom:** Arama çok yavaş.
   - **Muhtemel neden:** Büyük dataset veya search performansı.
   - **Çözüm:** Daha spesifik arama; page size düşür.
   - **Doğrulama:** Yanıt süresi düşer.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI’daki bazı ileri seviye player aksiyonları 404/501 ile fail.
   - **Muhtemel neden:** UI’da endpoint çağrısı var; backend build’de route yok.
   - **Impact:** İlgili aksiyon bloklanır; temel list/detail/update/disable çalışabilir.
   - **Admin Workaround:** No admin-side workaround (endpoint yoksa).
   - **Escalation Package:**
     - Method + path: DevTools → Network’ten alın
     - Request sample: DevTools’tan cURL export
     - Expected vs actual: expected 200/204, actual 404
     - Log: backend log’larda `player` + missing path ara
   - **Resolution Owner:** Backend
   - **Verification:** Endpoint 200 döner ve UI aksiyonu çalışır.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Search sonuç döndürür.
- Player detail açılır.
- Status değişiklikleri refresh sonrası kalıcıdır.

### 8.2 System → Logs
- Player endpoint’lerinde error var mı kontrol et.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `players`
  - `Player not found`
  - `tenant_id`

### 8.4 System → Audit Log
- Beklenen event’ler (varsa): `player.create`, `player.update`, `player.disabled`.

### 8.5 DB audit (varsa)
- `player` tablosu: status ve tenant_id.
- `auditevent`: actor + action + target_id.

---

## 9) Güvenlik notları + geri dönüş

- Player disable yüksek etkili bir kontroldür. Reason kaydı zorunlu.
- Geri dönüş: (destekleniyorsa) status’u tekrar active yap ve login doğrula.

---

## 10) İlgili linkler

- Finance: `/docs/new/tr/admin/core/finance.md`
- Withdrawals: `/docs/new/tr/admin/core/withdrawals.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
