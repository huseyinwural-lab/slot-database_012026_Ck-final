# CMS (TR)

**Menü yolu (UI):** System → CMS  
**Frontend route:** `/cms`  
**Sadece owner:** Evet (menu config)

---

## Ops Checklist (read first)

- CMS platform gibi görünse de tenant contexti doğrula (bazı içerikler tenant-scope olabilir).
- Publish/unpublish gibi akışlar varsa: kanıtı **Audit Log** + **Logs** ile topla (varsa).
- CMSi kontrollü içerik güncellemesi için kullan; destek kanalı gibi kullanma.

---

## 1) Amaç ve kapsam

CMS, player tarafında görünen içerik sayfalarını (ör. Terms, Privacy, FAQ, landing content) yönetmek için admin arayüzüdür.

Bu build’de CMS UI `frontend/src/pages/CMSManagement.jsx` içinde.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin)
- Potansiyel Content Manager rolü (varsa)

> UI görünürlüğü: System → CMS menüsü `frontend/src/config/menu.js`’de owner-only.

---

## 3) UI genel görünüm

CMS sayfasında:
- Content page listesi
- Yeni sayfa oluşturma (title/slug/content)
- Sayfa düzenleme
- Sayfa silme
- Basit status göstergeleri

---

## 4) Temel akışlar (adım adım)

### 4.1 CMS sayfalarını listeleme
1) System → CMS aç.
2) Var olan sayfalar listeleniyor mu kontrol et.

**API çağrıları (backend):**
- `GET /api/v1/cms/pages`

### 4.2 CMS sayfası oluşturma
1) **Create Page** tıkla.
2) Doldur:
   - title
   - slug
   - content
3) Submit.

**API çağrıları:**
- `POST /api/v1/cms/pages`

### 4.3 CMS sayfası düzenleme
1) Bir sayfa seç.
2) İçeriği güncelle.
3) Kaydet.

**API çağrıları:**
- `PUT /api/v1/cms/pages/{page_id}`

### 4.4 CMS sayfası silme
1) Bir sayfa seç.
2) Delete tıkla.
3) Onayla.

**API çağrıları:**
- `DELETE /api/v1/cms/pages/{page_id}`

---

## 5) Operasyon notları

- Legal sayfalar için (Terms/Privacy) sıkı review + onay süreci kullan.
- Küçük ve geri alınabilir değişiklikleri tercih et.
- Audit yoksa, harici bir change log tut.

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** CMS listesi boş.
   - **Muhtemel neden:** henüz sayfa yok.
   - **Çözüm:** test sayfası oluştur.
   - **Doğrulama:** sayfa listede görünür.

2) **Belirti:** CMS list fetch 401.
   - **Muhtemel neden:** admin session süresi doldu.
   - **Çözüm:** tekrar login.
   - **Doğrulama:** GET 200 döner.

3) **Belirti:** CMS list fetch 403.
   - **Muhtemel neden:** rol yetkisiz.
   - **Çözüm:** platform owner ile dene; role entitlements tanımla.
   - **Doğrulama:** rol CMSe erişebilir.

4) **Belirti:** Create 409 / slug conflict.
   - **Muhtemel neden:** slug unique olmalı.
   - **Çözüm:** slug değiştir.
   - **Doğrulama:** create 201.

5) **Belirti:** Create/edit 422.
   - **Muhtemel neden:** title/slug/content zorunlu alanlar eksik.
   - **Çözüm:** UI field validation ekle.
   - **Doğrulama:** request success.

6) **Belirti:** Edit refresh sonrası persist etmiyor.
   - **Muhtemel neden:** PUT endpoint yok veya commit başarısız.
   - **Çözüm:** `PUT /api/v1/cms/pages/{id}` var mı ve commit ediyor mu kontrol et.
   - **Doğrulama:** refresh sonrası içerik güncel.

7) **Belirti:** Delete 404.
   - **Muhtemel neden:** id bulunamadı.
   - **Çözüm:** listeyi refresh et; retry.
   - **Doğrulama:** listeden kaybolur.

8) **Belirti:** Admin UIda içerik var ama player siteta bozuk.
   - **Muhtemel neden:** player site routeları CMS içeriğine bağlı değil.
   - **Çözüm:** public CMS consumption endpoint/SSR logic doğrula.
   - **Doğrulama:** player site içerik gösterir.

9) **Belirti:** CMS değişiklikleri için audit kanıtı yok.
   - **Muhtemel neden:** CMS routeları audited değil.
   - **Çözüm:** audit ekle veya change ticketlarıyla kanıt tut.
   - **Doğrulama:** Audit Log `cms.page.created/updated/deleted` gösterir.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Belirti:** CMS çalışıyor ama approval/publish workflow yok.
   - **Muhtemel neden:** sadece MVP CRUD.
   - **Etki:** review edilmemiş legal içerik güncelleme riski.
   - **Admin workaround:** manuel onay süreci (2-person review).
   - **Escalation paketi:** approval/publish state ürün gereksinimi.
   - **Resolution owner:** Product/Backend
   - **Doğrulama:** publish status + audit trail var.

2) **Belirti:** CMS endpointleri var ama tenant-scope değil.
   - **Muhtemel neden:** cms_page modelinde tenant_id yok.
   - **Etki:** cross-tenant içerik sızıntısı.
   - **Admin workaround:** CMSi platform-global kabul et.
   - **Escalation paketi:** data model requirementlarını netleştir.
   - **Resolution owner:** Backend
   - **Doğrulama:** sayfalar tenant contexte göre filtrelenir.

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Liste yüklenir.
- Create/update/delete stale state olmadan görünür.

### 8.2 System → Logs
- cms endpointlerinde 4xx/5xx yok.

### 8.3 System → Audit Log
- CMS değişiklikleri audit event üretir (varsa).

### 8.4 DB doğrulama
- `cms_pages` tablosu beklenen satırlara sahip.

---

## 9) Güvenlik notları + rollback

- CMS değişiklikleri player-facing; prod değişikliği gibi ele al.
- Rollback:
  - içeriği son iyi versiyona geri al
  - veya yeni sayfayı sil

---

## 10) İlgili linkler

- Logs: `/docs/new/tr/admin/system/logs.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
