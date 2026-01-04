# Tenants (TR)

**Menü yolu (UI):** System → Tenants  
**Frontend route:** `/tenants`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Save öncesi **tenant id + name** doğrula.
- Yıkıcı aksiyonlarda rollback yolu: (**disable geri alınabilir**, purge genelde alınamaz).
- Değişikliği UI’da ve **System → Audit Log**’da doğrula.
- Incident için request path + status code + `request_id` (varsa) topla.

---

## 1) Amaç ve kapsam

Tenants menüsü, platform owner’ın tenant lifecycle yönetim alanıdır: tenant oluşturma, tenant listesini görüntüleme, tenant feature flag’lerini ve menü görünürlük flag’lerini güncelleme.

> Bu menü en yüksek riskli alanlardan biridir: yanlış tenant üzerinde yapılan işlem prod operasyonu ve güvenlik sınırlarını etkileyebilir.

---

## 2) Kim kullanır / yetki gereksinimi

- **Sadece Platform Owner (super admin).**
- Tenant admin’lerin erişimi olmamalıdır.

---

## 3) Alt başlıklar / fonksiyon alanları

Mevcut UI’da (`frontend/src/pages/TenantsPage.jsx`):
- Tenant listesi (sayfalı)
- Tenant create (name, type, features)
- Tenant feature edit (feature flags)
- Tenant menu visibility flags edit (menu_flags)

Backend enforce da owner-only:
- `GET /api/v1/tenants/` owner ister.

---

## 4) Temel akışlar

### 4.1 Yeni tenant oluşturma (sadece Platform Owner)
1) System → Tenants aç.
2) **Tenant name** ve **type** gir.
3) Default **features** seç (can_use_game_robot, can_edit_configs, can_manage_bonus, can_view_reports).
4) Submit.

**Hard-stop yetki kuralı (backend):**
- `current_admin.is_platform_owner != true` ise → **403 Forbidden**.

**Audit (zorunlu):**
- `tenant.create.attempt` tüm denemelerde yazılır (success/failed/denied).
- Başarılı create için ayrıca `tenant.created` yazılır.

**API çağrıları (frontend’den gözlemlendi):**
- Create: `POST /api/v1/tenants/`

### 4.2 Tenant listesini görüntüleme
1) Tenant listesine bak.
2) Pagination (Previous/Next) kullan.

**API çağrıları:**
- List: `GET /api/v1/tenants/?page=<n>&page_size=<n>`

### 4.3 Tenant feature güncelleme
1) Tenant için **Edit Features** tıkla.
2) Feature toggle’larını değiştir.
3) Save.

**API çağrıları:**
- Update: `PATCH /api/v1/tenants/{tenant_id}` body `{ features: {...} }`

### 4.4 Menü görünürlük flag’leri (menu_flags)
Bu alan tenant bazında sidebar menülerinin görünür/gizli olmasını yönetir.

1) Edit modunda menu flag’leri toggle et.
2) Save.

**Notlar:**
- UI logic: `menu_flags[key] === false` ise menü gizlenir. Default “enabled”.

---

## 5) Saha rehberi (pratik ipuçları)

- Doğru tenant’ı (name + id) kontrol etmeden save etme.
- Feature flag’leri tenant entitlement’ı için “hard contract” olarak ele alın.
- Menu flag değişikliklerini Support/Ops ile koordine edin.

**Yapmayın:**
- Aktif incident sırasında Audit/Logs/Keys erişimini kaldırma.

---

## 6) Olası hatalar (semptom → muhtemel neden → çözüm → doğrulama)

> Minimum 8 madde (yüksek riskli operasyon alanı).

1) **Semptom:** “Tenant oluşturulamıyor”
   - Muhtemel neden: required field eksik; duplicate tenant name.
   - Çözüm: `name` boş değil; unique isim kullan.
   - Doğrulama: `POST /api/v1/tenants/` 200 döner ve tenant listede görünür.

2) **Semptom:** Tenant listesi boş/eksik
   - Muhtemel neden: platform owner değil; backend error.
   - Çözüm: admin platform owner mı kontrol et; Network’te `GET /api/v1/tenants/` response’a bak.
   - Doğrulama: list endpoint items + meta döner.

3) **Semptom:** Yanlış tenant’ta değişiklik yapıldı
   - Muhtemel neden: operatör yanlış satırı seçti.
   - Çözüm: değişiklikleri hemen geri al; incident notu düş.
   - Doğrulama: Audit Log’ta before/after ve tenant features karşılaştır.

4) **Semptom:** Tenant disable edildi ama kullanıcılar hâlâ erişiyor
   - Muhtemel neden: disable implement edilmemiş; token/session cache; sadece UI-level değişiklik.
   - Çözüm: backend enforce var mı doğrula; mümkünse session invalidation uygula.
   - Doğrulama: kullanıcı protected endpoint’lerde 401/403 alır.

5) **Semptom:** System tenant silinmeye çalışıldı
   - Muhtemel neden: operatör hatası.
   - Çözüm: ilerleme; guard davranışı (403/blocked) beklenir.
   - Doğrulama: aksiyon bloklanır ve (varsa) audit’te attempted/denied görünür.

6) **Semptom:** Tenant purge yanlışlıkla tetiklendi
   - Muhtemel neden: unsafe UI akışı / onay eksikliği.
   - Çözüm: incident olarak ele al; purge geri alınamazsa backup/restore prosedürü uygula.
   - Doğrulama: DB’de veri var/yok kontrolü + evidence üretimi.

7) **Semptom:** Tenant admin login olamıyor
   - Muhtemel neden: admin user tenant’a atanmadı; role yanlış; gerekli module için feature disabled.
   - Çözüm: Admin Users’te tenant_id + role doğrula.
   - Doğrulama: login başarılı ve capabilities doğru tenant/features döner.

8) **Semptom:** “Tenant features updated” ama UI davranışı değişmiyor
   - Muhtemel neden: capabilities cache; menu flag default logic; refresh gerek.
   - Çözüm: browser refresh; capabilities yeniden fetch.
   - Doğrulama: `GET /api/v1/tenants/capabilities` güncel features döner; menüler beklenildiği gibi görünür/gizlenir.

9) **Semptom:** Tenant değişikliklerinden sonra raporlar hâlâ görünüyor
   - Muhtemel neden: report caching/retention.
   - Çözüm: cache TTL kontrol et; raporu yeniden üret.
   - Doğrulama: raporlar latest tenant state’i yansıtır.

---

## 7) Çözüm adımları (adım adım)

1) Network kanıtı al (endpoint + status + payload).
2) Acting admin platform owner mı doğrula.
3) Save öncesi tenant id/name doğrula.
4) Yanlış değişiklik olduysa: hemen revert + incident/evidence pack.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Create sonrası tenant listede görünür.
- Feature toggle’ları refresh sonrası kalıcıdır.
- Menu flag değişimleri tenant için sidebar görünürlüğünü etkiler.

### 8.2 System → Logs
- Tenant update çağrıları etrafındaki error/timeout’lara bak.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `tenants`
  - `TENANT_EXISTS` / `TENANT_NOT_FOUND`
  - `capabilities`

### 8.4 System → Audit Log
- Backend kodundan gözlenen action’lar:
  - `tenant.created`
  - `tenant.feature_flags_changed`
  - `TENANT_POLICY_UPDATED` (payments policy)

### 8.5 DB audit (varsa)
- Kanonik tablolar:
  - `tenant` (features JSON)
  - `auditevent` (tenant lifecycle change)

---

## 9) Güvenlik notları + geri dönüş (zorunlu)

### 9.1 System tenant koruması (kritik)
- **System tenant** hem UI hem backend seviyesinde korunmalıdır.
- Beklenen garantiler:
  - UI’dan hard-delete yapılamaz
  - attempt bloklanır ve audit edilebilir olmalıdır

### 9.2 Geri dönüş kuralları
- **Disable** (varsa) geri alınabilir (re-enable).
- **Purge/hard delete** (varsa) çoğunlukla geri alınamaz.
  - Recovery için backup/restore prosedürü kullanılır (Ops manual).

---

## 10) İlgili linkler

- Admin Users (tenant admin atama): `/docs/new/tr/admin/system/admin-users.md`
- Break-glass (tüm admin lockout): `/docs/new/tr/runbooks/break-glass.md`
- Backup/restore politikası: `/docs/new/tr/guides/ops-manual.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
