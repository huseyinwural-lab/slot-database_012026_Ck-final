# Bonuses (TR)

**Menü yolu (UI):** Operations → Bonuses  
**Frontend route:** `/bonuses`  
**Feature flag (UI):** `can_manage_bonus`  

---

## Ops Checklist (read first)

- Bonus’lar para eşdeğeridir (promo bakiye). Finansal değişiklik gibi ele al.
- Her create/toggle/grant için:
  - **Reason** zorunlu (UI ister; backend enforce eder)
  - **Audit Log** kanıtı
  - **Logs** ile anomali izleme
- Abuse dalgasında Kill Switch ile bonuses modülünü durdur.

---

## 1) Amaç ve kapsam

Bonuses modülü:
- bonus campaign’ler (deposit match, free spins)
- status değişimi (activate/pause)
- player’a manuel bonus grant

Frontend: `frontend/src/pages/BonusManagement.jsx`.
Backend: `backend/app/routes/bonuses.py`.

---

## 2) Kim kullanır / yetki gereksinimi

- CRM/Retention Ops
- Fraud/Risk (abuse response)

Erişim:
- UI: `can_manage_bonus`
- Backend: admin auth + tenant context
- Backend reason enforcement: `require_reason`

---

## 3) Temel akışlar

### 3.1 Campaign listeleme
**API çağrıları:**
- `GET /api/v1/bonuses/campaigns`

### 3.2 Campaign oluşturma
1) **New Campaign**.
2) Doldur:
   - name
   - type (deposit_match / free_spins)
   - config: multiplier, wagering_mult, min_deposit
   - reason (audit)
3) Create.

**API çağrıları:**
- `POST /api/v1/bonuses/campaigns`

### 3.3 Campaign pause/activate
1) Pause/Activate tıkla.
2) Reason gir.

**API çağrıları:**
- `POST /api/v1/bonuses/campaigns/{id}/status`

> Not: Backend şu an `status` alanını embed string bekliyor; UI `{ status, reason }` gönderiyor.

### 3.4 Manuel grant
Backend’de var; UI’da olmayabilir.

**API çağrıları:**
- `POST /api/v1/bonuses/grant`

---

## 4) Operasyon notları

- Wagering multiplier çok yüksekse churn yaratabilir.
- Abuse sinyalleri:
  - tekrarlayan grant denemeleri
  - 409 conflict’ler
  - ani bonus balance artışları

---

## 5) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Bonuses menüsü görünmüyor.
   - **Muhtemel neden:** `can_manage_bonus` yok.
   - **Çözüm:** feature ver.
   - **Doğrulama:** menü görünür.

2) **Belirti:** Create 400 REASON_REQUIRED.
   - **Muhtemel neden:** reason yok.
   - **Çözüm:** body’de `reason` veya `X-Reason` header.
   - **Doğrulama:** POST success.

3) **Belirti:** Create 422.
   - **Muhtemel neden:** config numeric değil.
   - **Çözüm:** multiplier/wagering/min_deposit sayı olmalı.
   - **Doğrulama:** campaign oluşur.

4) **Belirti:** Liste beklenmedik şekilde boş.
   - **Muhtemel neden:** tenant context mismatch.
   - **Çözüm:** tenant impersonation header kontrol.
   - **Doğrulama:** listede campaign’ler görünür.

5) **Belirti:** Status change 422.
   - **Muhtemel neden:** backend embed `status` bekliyor.
   - **Çözüm:** backend’i `{ status, reason }` kabul edecek şekilde hizala.
   - **Doğrulama:** status değişir ve refresh sonrası kalır.

6) **Belirti:** Status change 400 REASON_REQUIRED.
   - **Muhtemel neden:** reason yok.
   - **Çözüm:** reason ekle.
   - **Doğrulama:** audit event oluşur.

7) **Belirti:** Grant 409.
   - **Muhtemel neden:** player/campaign için aktif grant zaten var.
   - **Çözüm:** bonus history kontrol; duplicate grant yapma.
   - **Doğrulama:** ikinci grant bloklanır.

8) **Belirti:** Bonus balance artar ama wagering requirement artmaz.
   - **Muhtemel neden:** player wallet update tutarsız.
   - **Çözüm:** player wallet logic doğrula.
   - **Doğrulama:** `wagering_remaining` güncellenir.

9) **Belirti:** Bonus değişiklikleri için audit kanıtı yok.
   - **Muhtemel neden:** audit entegrasyonu eksik.
   - **Çözüm:** audit.log_event çağrıları doğrula.
   - **Doğrulama:** Audit Log `BONUS_*` action’larını içerir.

---

## 6) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI status update body’si backend beklentisiyle uyuşmuyor.
   - **Muhtemel neden:** backend `status: str = Body(..., embed=True)`.
   - **Etki:** toggle 422 ile fail edebilir.
   - **Admin workaround:** yok.
   - **Escalation paketi:** `/bonuses/campaigns/{id}/status` 422 body.
   - **Resolution owner:** Backend
   - **Doğrulama:** backend `{ status, reason }` kabul eder.

2) **Belirti:** UI’da manuel grant ekranı yok.
   - **Muhtemel neden:** UI eksik.
   - **Etki:** ops güvenli grant yapamaz.
   - **Resolution owner:** Frontend/Product

---

## 7) Doğrulama (UI + Logs + Audit + DB)

### 7.1 UI
- Campaign tabloda görünür.
- Toggle status değiştirir.

### 7.2 System → Logs
- `/api/v1/bonuses/*` 4xx/5xx kontrol.

### 7.3 System → Audit Log
- `BONUS_CAMPAIGN_CREATE`, `BONUS_CAMPAIGN_STATUS_CHANGE`, `BONUS_GRANT`.

### 7.4 DB doğrulama
- `bonus_campaign` ve `bonus_grant` satırları.

---

## 8) Güvenlik notları + rollback

- Rollback:
  - campaign’i pause et
  - grant revoke (implement gerektirir)

---

## 9) İlgili linkler

- Kill Switch: `/docs/new/tr/admin/operations/kill-switch.md`
- Players: `/docs/new/tr/admin/core/players.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
