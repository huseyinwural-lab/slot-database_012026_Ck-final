# Dashboard (TR)

**Menü yolu (UI):** Core → Dashboard  
**Frontend route:** `/dashboard`  
**Sadece owner:** Hayır  

---

## Ops Checklist (read first)

- Tenant context + time range doğrula.
- KPI şüpheliyse: kaynağı menüden çapraz kontrol et (Finance/Players/Games).

---

## 1) Amaç ve kapsam

Dashboard, platform/tenant performansına üst seviye bakış sunar: KPI’lar, trend grafikleri ve (varsa) son aktivite özetleri. Amaç hızlı durum farkındalığı sağlamak ve operatörün hangi menüde derinleşeceğine karar vermesidir.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin): tenant context seçilerek tenant bazında görüntüler.
- Tenant Admin / Ops: tenant KPI’larını ve operasyonel sağlığı izler.
- Finance/Risk: sinyallere göre derin inceleme menülerine yönelir.

---

## 3) Alt başlıklar (varsa)

Tipik bölümler:
- KPI kartları (sayı/tutar)
- Grafikler (trend)
- Son aktivite tablosu (varsa)

---

## 4) Temel akışlar

### 4.1 Zaman aralığı değiştirme
1) Tarih aralığı / preset seç.
2) KPI ve grafiklerin yenilendiğini gözle.

### 4.2 Tenant’a göre filtre (platform owner)
1) Tenant context değiştir.
2) KPI’ların doğru tenant’a ait olduğunu tekrar kontrol et.

### 4.3 Export (varsa)
- Bazı deploy’larda widget bazlı export vardır; bazılarında yoktur.

---

## 5) Saha rehberi (pratik ipuçları)

- **Veri gecikmesi** beklenebilir: bazı metrikler eventual consistency ile gelir.
- Tek bir KPI şüpheliyse kaynak menüden çapraz kontrol et:
  - Deposit/withdrawal → Finance / Withdrawals
  - Oyuncu değişimleri → Players
  - Game activity → Games

**Bu menü ne zaman kullanılmamalı:**
- Case-level çözüm için. Dashboard sadece “nereden bakılmalı” kararı içindir.

---

## 6) Olası hatalar (semptom → muhtemel neden)

1) **Semptom:** Dashboard boş / sıfır görünüyor
   - Muhtemel neden: yanlış tenant context, seçilen aralıkta veri yok, veya backend API erişilemiyor.

2) **Semptom:** KPI değerleri raporlarla uyuşmuyor
   - Muhtemel neden: timezone farkı, farklı aggregation window, veya geciken ETL.

3) **Semptom:** Sayfa açılıyor ama grafikler yüklenmiyor
   - Muhtemel neden: tek bir widget endpoint’i fail olurken diğerleri başarılı.

4) **Semptom:** Yavaş açılıyor / timeout
   - Muhtemel neden: çok geniş zaman aralığı veya ağır aggregation.

5) **Semptom:** Dashboard endpoint’lerinde 401 Unauthorized
   - Muhtemel neden: admin session süresi doldu veya token geçersiz.

6) **Semptom:** Dashboard açılırken 403 Forbidden
   - Muhtemel neden: tenant/menu entitlement kaldırıldı veya owner-only enforcement yanlış çalışıyor.

7) **Semptom:** Tenant context değişince metrikler “zıplıyor”
   - Muhtemel neden: tenant context tutarlı uygulanmıyor; cache etkisi.

8) **Semptom:** Refresh sonrası dashboard hâlâ eski görünüyor
   - Muhtemel neden: cached aggregation, geciken pipeline veya browser cache.

---

## 7) Çözüm adımları (adım adım)

1) Tenant context ve zaman aralığını doğrula.
2) Refresh et; DevTools → Network’te fail eden çağrıları kontrol et.
3) Tek endpoint fail ediyorsa status code + path’i alıp backend log’larına bak.
4) Daha küçük zaman aralığı dene.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Zaman aralığı değişince değerler değişmeli.
- İlgili deep-dive menülerle çapraz kontrol yapılmalı.

### 8.2 App / container log
- Endpoint path ve timeframe ile ara.
- Varsa `x-request-id` ile korelasyon yap.

### 8.3 Audit Log
- Dashboard genelde read-only; audit event beklenmez.

### 8.4 Database doğrulama (gerekiyorsa)
- Dashboard view problemlerinde genelde gerekmez.

---

## 9) Güvenlik notları

- Finansal KPI’lar hassas olabilir; erişimi role göre sınırla.

---

## 10) İlgili linkler

- `/docs/new/tr/admin/core/players.md`
- `/docs/new/tr/admin/core/finance.md`
- `/docs/new/tr/admin/system/reports.md`
- `/docs/new/tr/guides/common-errors.md`
