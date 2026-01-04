# Approval Queue (TR)

**Menü yolu (UI):** Risk & Compliance → Approval Queue  
**Frontend route:** `/approvals`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Approval aksiyonları yüksek risklidir; **kim, neyi, neden onayladı** mutlaka kayıt altına alınmalı.
- Her karar için:
  - request path + response (DevTools → Network)
  - **Audit Log** kanıtı (varsa)
  - hata için **Logs**
- Pending görünmüyorsa tenant context ve backend filter kontrol et.

---

## 1) Amaç ve kapsam

Approval Queue, dual-control / compliance onay süreçlerini yönetir.

Bu build’de UI: `frontend/src/pages/ApprovalQueue.jsx`.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin)
- Compliance / Finance onaylayıcıları (rol sistemi varsa)

---

## 3) Alt başlıklar / tab’lar (UI)

ApprovalQueue.jsx tab’ları:
- Pending
- Approved
- Rejected
- Policies (rules)
- Delegations (coming soon)

---

## 4) Temel akışlar

### 4.1 Pending request’leri görme
1) Approval Queue aç.
2) **Pending** tab’ı.

**API çağrıları (UI’ın kullandığı):**
- `GET /api/v1/approvals/requests?status=pending`

### 4.2 Approve / reject
1) Bir request seç.
2) Not ekle.
3) Approve veya Reject.

**API çağrıları:**
- `POST /api/v1/approvals/requests/{id}/action` body `{ action: "approve"|"reject", note: "..." }`

---

## 5) Saha rehberi (pratik ipuçları)

- Onaylar mutlaka şunlara bağlanmalı:
  - policy/rule
  - SLA
  - evidence paketi (link/screenshot/log)
- Red sebeplerini standardize et.

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Pending listesi sürekli boş.
   - **Muhtemel neden:** request yok; veya backend yanlış filtreliyor.
   - **Çözüm:** seed kontrol; tenant_id filter kontrol.
   - **Doğrulama:** GET satır döner.

2) **Belirti:** Approved/Rejected tab’ları da Pending gösteriyor.
   - **Muhtemel neden:** backend `status` query param’ını görmezden geliyor.
   - **Çözüm:** status filtering implement et.
   - **Doğrulama:** her tab doğru subset’i gösterir.

3) **Belirti:** Approve/Reject 422.
   - **Muhtemel neden:** backend `action` embed bekler ve `note` kabul etmez.
   - **Çözüm:** request body schema hizala (veya backend note kabul etsin).
   - **Doğrulama:** action 200.

4) **Belirti:** Approve/Reject 404.
   - **Muhtemel neden:** id bulunamadı.
   - **Çözüm:** listeyi refresh et; retry.
   - **Doğrulama:** item Pending’den çıkar.

5) **Belirti:** Delegations tab’ı Coming Soon.
   - **Muhtemel neden:** feature yok.
   - **Çözüm:** placeholder kabul et.
   - **Doğrulama:** (future) endpoint var.

6) **Belirti:** Policies tab 404.
   - **Muhtemel neden:** `/api/v1/approvals/rules` implement değil.
   - **Çözüm:** endpoint ekle veya tab’ı gizle.
   - **Doğrulama:** policies listesi yüklenir.

7) **Belirti:** approvals endpoint’lerinde 401/403.
   - **Muhtemel neden:** auth expired / rol yetkisiz.
   - **Çözüm:** tekrar login; owner ile dene.
   - **Doğrulama:** GET/POST 200.

8) **Belirti:** Approval için audit kanıtı yok.
   - **Muhtemel neden:** approve/reject audited değil.
   - **Çözüm:** audit event ekle.
   - **Doğrulama:** **Audit Log** `approval.request.approved/rejected` içerir.

9) **Belirti:** SLA görünmüyor.
   - **Muhtemel neden:** model SLA metadata tutmuyor.
   - **Çözüm:** alan ekle; UI göster.
   - **Doğrulama:** SLA görünür ve breach uyarısı var.

---

## 7) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI status bazlı liste ister, backend hep pending döner.
   - **Muhtemel neden:** `backend/app/routes/approvals.py` `status == "pending"` hardcode.
   - **Etki:** Approved/Rejected history yanlış.
   - **Admin workaround:** yok.
   - **Escalation paketi:**
     - `GET /api/v1/approvals/requests?status=approved`
     - beklenen: approved list; gerçek: pending list
     - anahtar kelime: `approvals/requests`
   - **Resolution owner:** Backend
   - **Doğrulama:** status query param uygulanır.

2) **Belirti:** UI `{ action, note }` yollar; backend sadece embed `action` kabul eder.
   - **Muhtemel neden:** backend `action: str = Body(..., embed=True)`.
   - **Etki:** Approve/Reject 422 ile kullanılamaz.
   - **Admin workaround:** yok.
   - **Escalation paketi:** 422 response body.
   - **Resolution owner:** Backend
   - **Doğrulama:** backend UI body’yi kabul eder; note saklanır.

3) **Belirti:** Policies/Delegations endpoint’leri yok.
   - **Muhtemel neden:** `/api/v1/approvals/rules` ve `/api/v1/approvals/delegations` implement değil.
   - **Etki:** approval governance eksik.
   - **Admin workaround:** policies’i harici tut.
   - **Resolution owner:** Backend/Product

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Approve/Reject sonrası item Pending’den çıkar.

### 8.2 System → Logs
- approvals endpoint’lerinde 4xx/5xx var mı kontrol.

### 8.3 System → Audit Log
- Approval event’leri görünmeli (varsa).

### 8.4 DB doğrulama
- `approval_requests` status güncellenir.

---

## 9) Güvenlik notları

- Approval privilege’dir; separation of duties uygula.
- Reason zorunlu olmalı.

---

## 10) İlgili linkler

- Risk Rules: `/docs/new/tr/admin/risk-compliance/risk-rules.md`
- Responsible Gaming: `/docs/new/tr/admin/risk-compliance/responsible-gaming.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
