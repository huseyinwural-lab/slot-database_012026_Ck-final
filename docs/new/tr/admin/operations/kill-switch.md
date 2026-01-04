# Kill Switch (TR)

**Menü yolu (UI):** Operations → Kill Switch  
**Frontend route:** `/kill-switch`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Apply öncesi tenant + module scope doğrula.
- Reason + blast radius + rollback koşullarını kaydet.
- 503 davranışı ve **Audit Log** kanıtını doğrula.
- Güvenli olur olmaz rollback: Enabled yap ve endpoint recovery kontrol.

---

## 1) Amaç ve kapsam

Kill Switch, belirli bir tenant için belirli modülleri (ve deploy’a göre global seviyeyi) acil durumda devre dışı bırakmaya yarar. Fraud dalgası, provider outage veya runaway maliyetlerde hızlı mitigasyon için kullanılır.

---

## 2) Kim kullanır / yetki gereksinimi

- Sadece Platform Owner (super admin).
- Yüksek blast-radius olduğu için erişimi sıkı kontrol edilmelidir.

---

## 3) Alt başlıklar / fonksiyon alanları

Mevcut UI’da (`frontend/src/pages/KillSwitchPage.jsx`):
- Tenant seçimi
- Module seçimi (crm, affiliates, experiments, kill_switch)
- State seçimi (Enabled / Disabled)
- Apply

Backend route’ları:
- Status: `GET /api/v1/kill-switch/status`
- Tenant modül kill switch: `POST /api/v1/kill-switch/tenant`

---

## 4) Temel akışlar

### 4.1 Tenant için modül disable
1) Doğru tenant üzerinde olduğunu doğrula.
2) Disable edilecek **Module** seç.
3) State’i **Disabled (503)** yap.
4) **Apply**.

**API çağrıları (frontend’den gözlemlendi):**
- `POST /api/v1/kill-switch/tenant` body `{ tenant_id, module_key, disabled }`

### 4.2 Modülü tekrar enable
1) Aynı tenant + module seç.
2) State’i **Enabled** yap.
3) Apply.

### 4.3 Karar rehberi (ne zaman kullanılır?)
- Şu durumlarda:
  - mali kayıp/fraud riski
  - provider outage’ın zincirleme hata yaratması
- Rutin bug’ları gizlemek için kullanılmaz.

---

## 5) Saha rehberi (pratik ipuçları)

- Mutlaka kayıt altına al:
  - tenant
  - module
  - neden
  - blast radius
  - rollback koşulları
- En dar kapsamı uygula (tenant + module).

**Yapmayın:**
- Recovery planı olmadan kill_switch modülünü de disable etmek.

---

## 6) Olası hatalar (semptom → muhtemel neden → çözüm → doğrulama)

> Minimum 8 madde (incident aracıdır).

1) **Semptom:** Incident sonrası switch açık kaldı
   - Muhtemel neden: post-incident checklist yok.
   - Çözüm: enable/disable checklist’i ve sorumlu belirle.
   - Doğrulama: modül re-enable; ticket hacmi normale döner.

2) **Semptom:** Yanlış tenant’ta açıldı
   - Muhtemel neden: tenant context karıştı.
   - Çözüm: hemen geri al; incident notu oluştur.
   - Doğrulama: audit kanıtında yanlış değişiklik + revert görünür.

3) **Semptom:** Beklenen modül durmadı
   - Muhtemel neden: backend enforcement yok; cache.
   - Çözüm: enforcement middleware var mı doğrula; gerekirse servisleri yeniden başlat.
   - Doğrulama: bloklanan istekler 503 döner ve log’larda gating görünür.

4) **Semptom:** Beklenmeyen modüller de durdu
   - Muhtemel neden: yanlış module_key veya global etki.
   - Çözüm: Enabled’a geri al; doğru modülü seç.
   - Doğrulama: etkilenmemesi gereken modüller normale döner.

5) **Semptom:** Withdrawal durdu ama deposit de durdu
   - Muhtemel neden: yanlış module key veya shared dependency.
   - Çözüm: scope’u düzelt; modül sınırlarını doğrula.
   - Doğrulama: sadece hedeflenen endpoint’ler bloklanır.

6) **Semptom:** Admin erişimi de kesildi
   - Muhtemel neden: kill switch admin route’larına da uygulanıyor veya auth katmanı etkileniyor.
   - Çözüm: switch’i geri al; lockout varsa break-glass.
   - Doğrulama: admin UI yeniden erişilebilir.

7) **Semptom:** Apply 403 döndürüyor
   - Muhtemel neden: platform owner değil veya tenant feature disabled.
   - Çözüm: rolü doğrula; tenant capabilities kontrol et.
   - Doğrulama: platform owner ile apply başarı.

8) **Semptom:** Apply 200 ama davranış değişmedi
   - Muhtemel neden: client cache; downstream enforcement yok.
   - Çözüm: client refresh; backend enforcement doğrulaması.
   - Doğrulama: bloklanan istekler sürekli 503 döner.

9) **Semptom:** Kill switch için audit kanıtı yok
   - Muhtemel neden: audit event implement edilmedi.
   - Çözüm: kill switch toggle audit edilsin; geçici olarak container log ile kanıt üret.
   - Doğrulama: Audit Log’ta event veya log’larda timestamp’lı kanıt.

---

## 7) Çözüm adımları (adım adım)

1) Incident şiddetini ve scope’u belirle.
2) Tenant + module seç.
3) Disabled uygula.
4) 503 davranışını doğrula ve kanıt topla.
5) Support/CRM ile iletişim.
6) Stabil olunca enable et ve recovery doğrula.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Kill switch ekranında state doğru görünür.

### 8.2 System → Logs
- Blocked request / 503 spike ara.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `kill_switch`
  - `disabled` / `503`
  - module key (crm/affiliates/experiments)

### 8.4 System → Audit Log
- Beklenen audit event (implementasyona göre): `kill_switch.toggled`.

### 8.5 DB audit (varsa)
- Mevcut implementasyonda kill switch’ler `tenant.features.kill_switches` (JSON) altında tutulur.
- Tenant features state’i UI ile eşleşmeli.

---

## 9) Güvenlik notları + geri dönüş

- Kill switch yüksek blast-radius taşır.
- Geri dönüş prosedürü (zorunlu):
  1) State’i Enabled yap.
  2) Endpoint’lerin geri geldiğini doğrula.
  3) Client cache veya residual bloklama kalmadığını kontrol et.

---

## 10) İlgili linkler

- Tenants (tenant seçimi güvenliği): `/docs/new/tr/admin/system/tenants.md`
- Break-glass: `/docs/new/tr/runbooks/break-glass.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
