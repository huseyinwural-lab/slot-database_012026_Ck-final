# Simulator (TR)

**Menü yolu (UI):** System → Simulator  
**Frontend route:** `/simulator`  
**Sadece owner:** Hayır (feature-gated)  

---

## 1) Amaç ve kapsam

Simulator (Simulation Lab), senaryo kurma, simülasyon çalıştırma ve sonuçları inceleme amacıyla kullanılır (game math, bonus etkisi, risk senaryoları vb.).

> Güvenlik kuralı: simülasyonlar real-money prod akışlarını etkilememelidir.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner: genellikle erişebilir.
- Tenant admin: sadece `can_use_game_robot` feature’ı aktifse.

Gözlemlenen gating:
- UI menü `feature: can_use_game_robot` ister.
- Backend’de `/api/v1/simulator/` stub ve feature check var.

---

## 3) Alt başlıklar / sekmeler

Mevcut UI’da (`frontend/src/pages/SimulationLab.jsx`):
- Overview
- Game Math
- Portfolio (UI placeholder)
- Bonus
- Cohort/LTV (UI placeholder)
- Risk (UI placeholder)
- RG (UI placeholder)
- A/B Sandbox (UI placeholder)
- Scenario Builder (UI placeholder)
- Archive

Gözlemlenen data endpoint’i:
- Runs listesi: `GET /api/v1/simulation-lab/runs`

**Önemli implementasyon notu:** Backend’de `routes/simulation_lab.py` stub durumda, bu yüzden `/api/v1/simulation-lab/*` endpoint’leri **404 Not Found** dönebilir.

---

## 4) Temel akışlar

### 4.1 Senaryo oluşturma / konfigürasyon
1) İlgili simulator sekmesini seç (örn. Game Math, Bonus).
2) Input’ları konfigüre et.
3) Kaydet veya draft tut (implementasyona bağlı).

### 4.2 Simülasyon çalıştırma
1) Senaryo için run aksiyonunu başlat.
2) Overview/Archive ekranından status izle.

### 4.3 Sonuçları okuma
1) Completed run’ı aç.
2) Temel metrikleri yorumla.

### 4.4 Cleanup / reset
- Retention politikasına göre draft ve eski run’ları temizle.

---

## 5) Saha rehberi (pratik ipuçları)

- Senaryoları mutlaka şu bilgilerle etiketle:
  - amaç
  - varsayımlar
  - dataset/versiyon
- Hız için senaryoları küçük tut.
- Peak incident sırasında zorunlu değilse simülasyon aracı kullanma.

**Prod’da şunun için kullanmayın:**
- Rollback planı olmadan “değişiklik doğrulama”.

---

## 6) Olası hatalar (semptom → muhtemel neden → çözüm → doğrulama)

> Minimum 8 madde.

1) **Semptom:** Run anında fail
   - Muhtemel neden: required input/config eksik.
   - Çözüm: required alanları doldur; tekrar çalıştır.
   - Doğrulama: status draft → running geçer.

2) **Semptom:** Runs listesi yüklenmiyor
   - Muhtemel neden: `/api/v1/simulation-lab/runs` endpoint’i yok.
   - Çözüm: backend’in Simulation Lab route’larını desteklediğini doğrula.
   - Doğrulama: endpoint array döner ve UI render eder.

3) **Semptom:** Run tamamlandı ama sonuçlar görünmüyor
   - Muhtemel neden: UI cache veya results payload eksik.
   - Çözüm: refresh; run detail endpoint’i varsa kontrol et.
   - Doğrulama: results panel dolu.

4) **Semptom:** Beklenmeyen sonuç
   - Muhtemel neden: math asset mismatch; yanlış dataset.
   - Çözüm: math asset versiyonunu doğrula; doğru input’la tekrar çalıştır.
   - Doğrulama: baseline ile uyum.

5) **Semptom:** Performans sorunu
   - Muhtemel neden: senaryo çok büyük; worker limitleri.
   - Çözüm: senaryoyu küçült; düşük trafikte çalıştır.
   - Doğrulama: runtime düşer ve tamamlanır.

6) **Semptom:** 403 Forbidden
   - Muhtemel neden: `can_use_game_robot` feature disabled.
   - Çözüm: System → Tenants’ten feature enable et; yeniden login.
   - Doğrulama: menü erişilir ve endpoint 200 döner.

7) **Semptom:** “Run başladı ama bitmiyor”
   - Muhtemel neden: worker down veya job stuck.
   - Çözüm: backend worker sağlık + log kontrol; cancel/retry.
   - Doğrulama: status completed/failed’e geçer ve reason görünür.

8) **Semptom:** Sandbox/prod karışıklığı
   - Muhtemel neden: prod varsayımlarla simülasyon çalıştırma.
   - Çözüm: environment ayrımı; sandbox constraint enforce.
   - Doğrulama: prod’a yan etki yok.

9) **Semptom:** Export hatası
   - Muhtemel neden: export endpoint yok.
   - Çözüm: desteklenen download mekanizması kullan.
   - Doğrulama: export dosyası üretilir.

---

## 7) Çözüm adımları (adım adım)

1) Kullanıcı/tenant `can_use_game_robot` sahip mi doğrula.
2) Fail eden endpoint + status al.
3) Job runner/worker sorunları için backend log’larına bak.
4) Senaryo karmaşıklığını azalt.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Overview runs listesini göstermeli.
- Status badge’ler doğru geçiş yapmalı.

### 8.2 System → Logs
- Job failure ve tekrarlayan error’ları kontrol et.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `simulation`
  - `simulator`
  - `run`
  - `job` / `worker`

### 8.4 System → Audit Log
- Beklenen audit event (varsa): `simulation.executed`.

### 8.5 DB audit (varsa)
- Run saklama deploy’a göre değişir.
- Kanıt: run id, actor, inputs, timestamp.

---

## 9) Güvenlik notları + geri dönüş

- Simülasyon özellikleri sandbox olmalıdır.
- Simülasyon prod davranışını etkiliyorsa:
  - simulator feature’ı disable et
  - kanıt topla
  - incident sürecini uygula

---

## 10) İlgili linkler

- Tenants (feature enable): `/docs/new/tr/admin/system/tenants.md`
- Math Assets: `/docs/new/tr/admin/game-engine/math-assets.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
