# CRM & Comms (TR)

**Menü yolu (UI):** Operations → CRM & Comms  
**Frontend route:** `/crm`  
**Feature flag (UI):** `can_use_crm`  

---

## Ops Checklist (read first)

- Tenant context’i doğrula; iletişimler müşteri-facing olabilir ve regüle edilir.
- Her “send” için:
  - campaign id + segment + template bilgilerini kayıt altına al
  - **Logs** ve **Audit Log** ile doğrula (varsa)
- Modül disabled ise:
  - Operations → Kill Switch’te `crm` state kontrol et
  - `can_use_crm` capability var mı bak.

---

## 1) Amaç ve kapsam

CRM & Comms, outbound iletişimleri yönetir:
- campaigns
- message templates
- player segments
- channels/providers

Frontend: `frontend/src/pages/CRM.jsx`.

Backend: `/api/v1/crm/*` mevcut; ancak bazı route’lar stub ve boş liste döndürüyor.

---

## 2) Kim kullanır / yetki gereksinimi

- CRM Ops / Retention
- Compliance (review)

Erişim:
- UI: `can_use_crm`
- Backend: `enforce_module_access(..., module_key="crm")`

---

## 3) Alt başlıklar / tab’lar (UI)

CRM.jsx tab’ları:
- Campaigns
- Templates
- Segments
- Channels

---

## 4) Temel akışlar

### 4.1 Campaign listesi
**API çağrıları:**
- `GET /api/v1/crm/campaigns`

### 4.2 Campaign oluşturma (draft)
1) **New Campaign** tıkla.
2) Doldur:
   - name
   - channel (email/sms/push)
   - segment_id (mock id)
   - template_id (mock id)
3) Create.

**API çağrıları:**
- `POST /api/v1/crm/campaigns`

### 4.3 Campaign gönderme
1) Campaigns tablosunda **Send**.

**API çağrıları:**
- `POST /api/v1/crm/campaigns/{campaign_id}/send`

### 4.4 Templates / Segments / Channels görüntüleme
**API çağrıları:**
- `GET /api/v1/crm/templates`
- `GET /api/v1/crm/segments`
- `GET /api/v1/crm/channels`

---

## 5) Operasyon notları

- Compliance review gerektirenler:
  - bonus / VIP offer
  - jurisdiction kısıtları
  - unsubscribe gereksinimleri
- Yeni segmentlerde dry-run tercih et (varsa).

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** CRM menüsü görünmüyor.
   - **Muhtemel neden:** `can_use_crm` enabled değil.
   - **Çözüm:** feature ver.
   - **Doğrulama:** menü görünür.

2) **Belirti:** CRM “Coming soon / Not implemented” gösteriyor.
   - **Muhtemel neden:** bazı tab endpoint’leri 404.
   - **Çözüm:** eksik endpoint’i implement et veya tab’ı kapat.
   - **Doğrulama:** tab veri yükler.

3) **Belirti:** Campaign listesi hep boş.
   - **Muhtemel neden:** backend stub `[]` dönüyor.
   - **Çözüm:** persistence implement.
   - **Doğrulama:** created campaign listede görünür.

4) **Belirti:** Create 403.
   - **Muhtemel neden:** kill switch veya entitlement yok.
   - **Çözüm:** Kill Switch’te `crm`; capability doğrula.
   - **Doğrulama:** POST 200/201.

5) **Belirti:** Send 500.
   - **Muhtemel neden:** provider entegrasyonu yok.
   - **Çözüm:** provider config; Logs incele.
   - **Doğrulama:** send queued.

6) **Belirti:** Send 200 ama delivery yok.
   - **Muhtemel neden:** async job/worker yok.
   - **Çözüm:** queue worker + delivery log.
   - **Doğrulama:** delivery receipt loglanır.

7) **Belirti:** Segment seçimi kafa karıştırıcı.
   - **Muhtemel neden:** mock id + segments endpoint boş.
   - **Çözüm:** gerçek segmentation modeli.
   - **Doğrulama:** segment dropdown dolu.

8) **Belirti:** Send/create için audit kanıtı yok.
   - **Muhtemel neden:** CRM route’ları audited değil.
   - **Çözüm:** audit event ekle.
   - **Doğrulama:** Audit Log `crm.campaign.*` içerir.

9) **Belirti:** Unsubscribe compliance sağlanmıyor.
   - **Muhtemel neden:** opt-out enforcement yok.
   - **Çözüm:** opt-out list; unsubscribe link.
   - **Doğrulama:** opt-out honored.

---

## 7) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** Templates/Segments/Channels endpoint’leri var ama hep boş.
   - **Muhtemel neden:** `backend/app/routes/crm.py` stub `[]`.
   - **Etki:** CRM prod seviyesinde değil.
   - **Admin workaround:** templates/segments harici tutulur.
   - **Escalation paketi:** data model + persistence.
   - **Resolution owner:** Backend

2) **Belirti:** Send gerçek provider’lara bağlı değil.
   - **Muhtemel neden:** email/sms/push entegrasyonu yok.
   - **Etki:** mesajlar müşteriye gitmez.
   - **Resolution owner:** Backend/Product

---

## 8) Doğrulama (UI + Logs + Audit)

### 8.1 UI
- Create success.
- Send queued.

### 8.2 System → Logs
- `/api/v1/crm/*` 4xx/5xx kontrol.

### 8.3 System → Audit Log
- create/send event’leri (varsa).

---

## 9) Güvenlik notları

- CRM içeriğini regüle kabul et.
- Logs/Audit’te ham mesaj body tutmaktan kaçın.

---

## 10) İlgili linkler

- Kill Switch: `/docs/new/tr/admin/operations/kill-switch.md`
- Support: `/docs/new/tr/admin/operations/support.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
