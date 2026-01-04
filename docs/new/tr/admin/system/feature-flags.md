# Feature Flags (TR)

**Menü yolu (UI):** System → Feature Flags  
**Frontend route:** `/experiments`  
**Sadece owner:** Evet (owner + `experiments` module access)  

---

## Ops Checklist (read first)

- Toggle öncesi: **tenant context** ve blast radius’ı doğrula.
- Rollout’ta: önce **düşük yüzde** veya kontrollü segment ile başla; error rate izle.
- “Flag etkisi görünmüyor” ise: refresh, cache/propagation kontrol, backend response success mi bak.
- Yanlış flag prod’u bozduysa: hemen rollback (toggle off) ve audit kanıtı topla.

---

## 1) Amaç ve kapsam

Feature Flags, feature exposure’u runtime’da yönetmek (enable/disable), experiment ve targeting için kullanılır. Kontrollü rollout, incident mitigasyon ve staged release amaçlıdır.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin)
- Backend enforce: `experiments` module access

---

## 3) Alt başlıklar / sekmeler

Mevcut UI (`frontend/src/pages/FeatureFlags.jsx`):
- Feature Flags
- Experiments
- Segments
- Analytics
- Results
- Audit Log (flags)
- Env Compare
- Groups

UI’ın kullandığı backend route’lar:
- `GET /api/v1/flags/`
- `POST /api/v1/flags/` (create)
- `POST /api/v1/flags/{flag_id}/toggle`
- `GET /api/v1/flags/experiments`
- `POST /api/v1/flags/experiments/{id}/start|pause`
- `GET /api/v1/flags/segments`
- `GET /api/v1/flags/audit-log`
- `GET /api/v1/flags/environment-comparison`
- `GET /api/v1/flags/groups`
- `POST /api/v1/flags/kill-switch`

---

## 4) Rollout ve targeting modeli (nasıl düşünmeli?)

Bu UI “product-style” feature flag modelini hedefler:
- Percentage rollout (kademeli exposure)
- Segment bazlı exposure (kontrollü cohort)

Operasyonel öneri:
- Segment veya düşük yüzde ile başla.
- KPI/error izle.
- Kademeli genişlet.

---

## 5) Temel akışlar (adım adım)

### 5.1 Flag toggle
1) Feature Flags sekmesini aç.
2) Flag üzerindeki power ikonuna tıkla.

**API çağrıları:**
- Toggle: `POST /api/v1/flags/{flag_id}/toggle`

### 5.2 Kill switch (flags)
1) **Kill Switch** tıkla.
2) Onayla.

**API çağrıları:**
- `POST /api/v1/flags/kill-switch`

### 5.3 Flag oluşturma
1) **Create Flag** tıkla.
2) flag_id, name, description, type, scope, environment, group gir.
3) Save.

**API çağrıları:**
- Create: `POST /api/v1/flags/`

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** “Flag etkisi görülmüyor”.
   - **Muhtemel neden:** cache/propagation gecikmesi; client reload gerek.
   - **Çözüm:** refresh; TTL bekle; downstream servis reload kontrol.
   - **Doğrulama:** davranış refresh sonrası tutarlı değişir.

2) **Semptom:** Toggle success ama hiçbir şey değişmiyor.
   - **Muhtemel neden:** backend stub (persist etmiyor).
   - **Çözüm:** backend gap kabul et; prod gating için güvenme.
   - **Doğrulama:** backend fix sonrası list state’i reload’da korunur.

3) **Semptom:** Yanlış flag prod’u bozdu.
   - **Muhtemel neden:** unsafe rollout; staging doğrulaması yok.
   - **Çözüm:** hemen rollback (toggle off); iletişim; incident aç.
   - **Doğrulama:** error rate düşer ve davranış normale döner.

4) **Semptom:** 403 Forbidden.
   - **Muhtemel neden:** owner değil veya tenant’ta `experiments` modülü yok.
   - **Çözüm:** owner admin; tenant modülünü enable.
   - **Doğrulama:** endpoint 200.

5) **Semptom:** Flag listesi hiç yüklenmiyor.
   - **Muhtemel neden:** endpoint error veya auth.
   - **Çözüm:** `/api/v1/flags/` response kontrol.
   - **Doğrulama:** liste yüklenir.

6) **Semptom:** Env Compare boş.
   - **Muhtemel neden:** stub endpoint veya veri yok.
   - **Çözüm:** bilgi amaçlı kabul; gerekirse escalate.
   - **Doğrulama:** compare endpoint diff döner.

7) **Semptom:** Segments listesi boş.
   - **Muhtemel neden:** segments implement edilmemiş.
   - **Çözüm:** backend gap.
   - **Doğrulama:** segments endpoint list döner.

8) **Semptom:** Audit tab boş.
   - **Muhtemel neden:** audit-log endpoint stub.
   - **Çözüm:** kanonik kanıt için System → Audit Log.
   - **Doğrulama:** `auditevent` flag aksiyonlarını içerir.

9) **Semptom:** Kill switch OK dönüyor ama etkisi yok.
   - **Muhtemel neden:** backend bu endpoint’i no-op tutuyor.
   - **Çözüm:** gerçek gating için Operations → Kill Switch.
   - **Doğrulama:** module kill switch istekleri bloklar.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Flag’ler persist etmiyor / listeler hep boş.
   - **Likely Cause:** Bu build’de `/api/v1/flags/*` route’ları safe stub olarak implement edilmiş (çoğu `[]`, toggle/create OK).
   - **Impact:** Feature Flags UI prod-grade rollout mekanizması olarak kullanılamaz.
   - **Admin Workaround:**
     - Incident gating için Operations → Kill Switch kullan.
     - Persist gelene kadar Feature Flags’i “bilgilendirme/deneme” olarak ele al.
   - **Escalation Package:**
     - HTTP method + path: `GET /api/v1/flags/`, `POST /api/v1/flags/`, `POST /api/v1/flags/{id}/toggle`
     - Expected vs actual: expected persistence; actual empty/no persistence
     - Log keyword: `flags`, `toggle`, `CREATED`, `TOGGLED`
   - **Resolution Owner:** Backend
   - **Verification:** toggle state’i reload sonrası korunur ve list state’i gösterir.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Flag listesi yüklenir.
- Toggle sonrası state değişimi görünür (persistence varsa).

### 8.2 System → Audit Log
- Flag aksiyonları (implement edildiyse) audit’te görünür.

### 8.3 System → Logs / container log
- `flags`, `toggle`, `experiments` ile ara.

### 8.4 DB audit (varsa)
- `featureflag`/`feature_flags` tabloları (varsa) ve `auditevent`.

---

## 9) Güvenlik notları + geri dönüş

- Yanlış flag prod’u bozabilir. Rollback anlık olmalı.

---

## 10) İlgili linkler

- Kill Switch: `/docs/new/tr/admin/operations/kill-switch.md`
- Tenants: `/docs/new/tr/admin/system/tenants.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
