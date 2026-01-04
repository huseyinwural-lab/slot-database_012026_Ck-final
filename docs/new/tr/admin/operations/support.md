# Support (TR)

**Menü yolu (UI):** Operations → Support  
**Frontend route:** `/support`  

---

## Ops Checklist (read first)

- Support işi closed-loop olmalı: ticket → aksiyon → kanıt → çözüm.
- Platform issue gördüğünüzde Diagnostics’ten Request ID alın.
- Her tab için backend endpoint’leri doğrula; bazıları şu an eksik.

---

## 1) Amaç ve kapsam

Support Center şunlar için operasyon konsoludur:
- ticket yönetimi
- chat oturumları
- knowledge base
- canned responses
- diagnostics (son Request ID)

Frontend: `frontend/src/pages/Support.jsx`.

---

## 2) Kim kullanır / yetki gereksinimi

- Support agent’leri
- Ops/Engineering (diagnostics)

---

## 3) Alt başlıklar / tab’lar (UI)

Support.jsx tab’ları:
- Overview (dashboard + diagnostics)
- Inbox (tickets)
- Live Chat (sessions)
- Help Center (KB)
- Config (canned responses + automations placeholder)

---

## 4) Temel akışlar

### 4.1 Diagnostics: son Request ID
1) Support → Overview.
2) Request ID kopyala.
3) Ops’a ilet (log korelasyonu).

**Kaynak:** local storage / interceptor (`supportDiagnostics`).

### 4.2 Ticket kuyruğu görüntüleme
1) Inbox.
2) Ticket seç.

**API çağrıları (UI):**
- `GET /api/v1/support/tickets`

### 4.3 Ticket cevaplama
1) Ticket seç.
2) Reply yaz.
3) Reply tıkla.

**API çağrıları (UI):**
- `POST /api/v1/support/tickets/{ticket_id}/message`

---

## 5) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Overview dashboard yüklenmiyor.
   - **Muhtemel neden:** `GET /api/v1/support/dashboard` yok.
   - **Çözüm:** endpoint implement et veya widget’ı gizle.
   - **Doğrulama:** KPI’lar görünür.

2) **Belirti:** Ticket listesi var ama reply 404.
   - **Muhtemel neden:** route mismatch: backend `/tickets/{id}/reply`, UI `/tickets/{id}/message` çağırıyor.
   - **Çözüm:** backend’i `/message` kabul edecek şekilde hizala veya UI’ı güncelle.
   - **Doğrulama:** reply persist eder; ticket status güncellenir.

3) **Belirti:** Prod’da ticket listesi boş.
   - **Muhtemel neden:** ticket yok veya tenant filter mismatch.
   - **Çözüm:** seed; tenant_id filter doğrula.
   - **Doğrulama:** GET liste döner.

4) **Belirti:** Live Chat tab’ı hep boş.
   - **Muhtemel neden:** `GET /api/v1/support/chats` yok.
   - **Çözüm:** endpoint implement.
   - **Doğrulama:** sessions görünür.

5) **Belirti:** KB tab’ı hep boş.
   - **Muhtemel neden:** `GET /api/v1/support/kb` yok.
   - **Çözüm:** KB endpoint’leri ekle.
   - **Doğrulama:** KB listesi görünür.

6) **Belirti:** Config (canned responses) fail.
   - **Muhtemel neden:** `GET/POST /api/v1/support/canned` yok.
   - **Çözüm:** canned endpoints implement.
   - **Doğrulama:** canned list güncellenir.

7) **Belirti:** Reply başarılı ama audit kanıtı yok.
   - **Muhtemel neden:** support route’ları audited değil.
   - **Çözüm:** message audit event.
   - **Doğrulama:** Audit Log `support.ticket.replied` içerir.

8) **Belirti:** Request ID boş.
   - **Muhtemel neden:** interceptor last error capture etmiyor.
   - **Çözüm:** axios interceptor `support:last_error` emit ediyor mu ve `support_last_error` yazıyor mu kontrol.
   - **Doğrulama:** hata sonrası Request ID görünür.

9) **Belirti:** support endpoint’lerinde 401/403.
   - **Muhtemel neden:** auth expired / permission.
   - **Çözüm:** tekrar login; support rolü.
   - **Doğrulama:** endpoint 200.

---

## 6) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI `/dashboard`, `/chats`, `/kb`, `/canned` kullanıyor; backend sadece `/tickets` ve `/tickets/{id}/reply` sağlıyor.
   - **Muhtemel neden:** `backend/app/routes/support.py` eksik.
   - **Etki:** Support Center tab’larının çoğu çalışmaz.
   - **Admin workaround:** harici ticketing; incident triage için diagnostics + Logs.
   - **Escalation paketi:**
     - Eksik endpoint’ler:
       - `GET /api/v1/support/dashboard`
       - `GET /api/v1/support/chats`
       - `GET /api/v1/support/kb`
       - `GET /api/v1/support/canned`
       - `POST /api/v1/support/canned`
       - `POST /api/v1/support/tickets/{id}/message` (veya `/reply` ile hizalama)
     - Anahtar kelime: `support/`
   - **Resolution owner:** Backend

---

## 7) Doğrulama (UI + Logs + Audit)

### 7.1 UI
- Ticket listesi gelir.
- Reply mesaj ekler.

### 7.2 System → Logs
- `support` endpoint hataları.

### 7.3 System → Audit Log
- support aksiyonları (varsa).

---

## 8) Güvenlik notları

- Support notları PII içerebilir; redaction uygula.
- Role bazlı erişim kısıtla.

---

## 9) İlgili linkler

- Logs: `/docs/new/tr/admin/system/logs.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
