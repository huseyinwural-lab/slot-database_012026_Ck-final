# KYC Verification (TR)

**Menü yolu (UI):** Operations → KYC Verification  
**Frontend route:** `/kyc`  
**Feature flag (UI):** `can_manage_kyc`  

---

## Ops Checklist (read first)

- Tenant context’i doğrula; KYC kararları oyuncuyu etkiler ve hukuken hassastır.
- Mutlaka kaydet:
  - karar (approve/reject)
  - reason
  - kanıt referansları
- Sonucu şuralardan doğrula:
  - **UI** (queue state)
  - **Audit Log** (varsa)
  - **Logs** (4xx/5xx / request_id)

---

## 1) Amaç ve kapsam

KYC Verification, kimlik doğrulama akışını yönetir:
- pending doğrulama kuyruğu
- doküman review sonuçları
- operasyon KPI’ları (pending/verified/rejected)

Frontend: `frontend/src/pages/KYCManagement.jsx`.

> Önemli: Bu repoda `/api/v1/kyc/*` backend modülü açıkça **MOCKED UI support** diye işaretli ve prod/staging’de kapalı olabilir.

---

## 2) Kim kullanır / yetki gereksinimi

- Support / KYC Ops
- Compliance

Erişim kontrolü:
- UI: `can_manage_kyc`
- Backend: `feature_required("can_manage_kyc")`

---

## 3) Alt başlıklar / fonksiyon alanları

KYCManagement UI:
- KPI kartları (dashboard)
- Verification queue
- Review modal (documents)

---

## 4) Temel akışlar

### 4.1 KYC dashboard görüntüleme
1) Operations → KYC Verification aç.
2) KPI’ları izle.

**API çağrıları (UI):**
- `GET /api/v1/kyc/dashboard`

### 4.2 Verification queue görüntüleme
1) Queue ekranına geç.

**API çağrıları:**
- `GET /api/v1/kyc/queue`

### 4.3 Doküman review
1) Queue item aç.
2) Dokümanları incele.
3) Status seç:
   - approved
   - rejected
4) Submit.

**API çağrıları:**
- `POST /api/v1/kyc/documents/{doc_id}/review`

---

## 5) Operasyon notları

- Yüksek riskli oyuncular için dual-control uygula (policy’ye bağlı).
- PII exposure minimum tutulmalı.
- Player profilindeki `kyc_status` ile queue tutarlı olmalı.

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** KYC menüsü görünmüyor.
   - **Muhtemel neden:** `can_manage_kyc` capability yok.
   - **Çözüm:** role/tenant’a feature ata.
   - **Doğrulama:** menü görünür; route açılır.

2) **Belirti:** Dashboard/queue endpoint’leri 404 dönüyor.
   - **Muhtemel neden:** environment’ta KYC mock guard kapalı.
   - **Çözüm:** mock sadece dev/test’te açık; staging/prod için gerçek KYC servisi implement.
   - **Doğrulama:** endpoint’ler 200.

3) **Belirti:** Pending oyuncular varken queue boş.
   - **Muhtemel neden:** filter mismatch (`kyc_status == pending`) veya tenant mismatch.
   - **Çözüm:** tenant_id filter + player kayıtları doğrula.
   - **Doğrulama:** queue oyuncuları döner.

4) **Belirti:** Doküman görselleri placeholder.
   - **Muhtemel neden:** MOCK document URL.
   - **Çözüm:** gerçek document storage entegrasyonu.
   - **Doğrulama:** gerçek doküman URL’leri yüklenir.

5) **Belirti:** Review submit 422.
   - **Muhtemel neden:** payload schema uyuşmuyor.
   - **Çözüm:** body’de `status` alanı `approved|rejected` olmalı.
   - **Doğrulama:** response güncel status döner.

6) **Belirti:** Review submit player için 404/yanlış güncelleme.
   - **Muhtemel neden:** mock doc_id gerçek player_id ile eşleşmiyor.
   - **Çözüm:** doğru KYC document modeli implement.
   - **Doğrulama:** doğru player güncellenir.

7) **Belirti:** Approved oyuncu hâlâ pending queue’da.
   - **Muhtemel neden:** status persist edilmedi veya cache.
   - **Çözüm:** DB commit doğrula; refresh.
   - **Doğrulama:** pending’den çıkar.

8) **Belirti:** Approve/reject için audit kanıtı yok.
   - **Muhtemel neden:** KYC endpoint’lerinde audit yok.
   - **Çözüm:** KYC kararları için audit event ekle.
   - **Doğrulama:** Audit Log `kyc.review.*` event’lerini içerir.

9) **Belirti:** KYC kararları jurisdiction rule’larıyla çelişiyor.
   - **Muhtemel neden:** compliance policy enforcement yok.
   - **Çözüm:** policy check + gerekirse Approval Queue.
   - **Doğrulama:** policy ihlalleri bloklanır ve loglanır.

---

## 7) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** Dev’de çalışır gibi, staging/prod’da görünmez.
   - **Muhtemel neden:** `backend/app/routes/kyc.py` açıkça **MOCKED** ve env flag ile guard’lı.
   - **Etki:** prod seviyesinde KYC workflow yok.
   - **Admin workaround:** yok.
   - **Escalation paketi:** gerçek provider entegrasyonu + data model.
   - **Resolution owner:** Backend/Product

2) **Belirti:** Document storage placeholder.
   - **Muhtemel neden:** documents tablosu/storage yok.
   - **Etki:** gerçek doküman review yapılamaz.
   - **Resolution owner:** Backend

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Review sonrası dashboard count’lar değişir.
- Approve/reject sonrası player pending’den çıkar.

### 8.2 System → Logs
- `/api/v1/kyc/*` hataları kontrol.

### 8.3 System → Audit Log
- KYC review event’leri (varsa).

### 8.4 DB doğrulama
- Player.kyc_status güncellenir.

---

## 9) Güvenlik notları + rollback

- Ham doküman görsellerini onaylı araçlar dışında paylaşma.
- Rollback genelde uygulanmaz; doğru onayla yeni review açılır.

---

## 10) İlgili linkler

- Players: `/docs/new/tr/admin/core/players.md`
- Approval Queue: `/docs/new/tr/admin/risk-compliance/approval-queue.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
