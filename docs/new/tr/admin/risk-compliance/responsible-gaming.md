# Responsible Gaming (TR)

**Menü yolu (UI):** Risk & Compliance → Responsible Gaming  
**Frontend route:** `/rg`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- RG aksiyonları kullanıcı koruma amaçlıdır ama hukuki olarak hassastır.
- Mutlaka kanıt topla:
  - request path + response (DevTools → Network)
  - aksiyon için **Audit Log** kaydı (varsa)
  - runtime hataları için **Logs**
- Exclusion kaldırma (“lift”) için onay süreci olmadan işlem yapma.

---

## 1) Amaç ve kapsam

Responsible Gaming (RG) player koruma kontrollerini uygular:
- deposit/loss/session limitleri
- geçici cool-off
- self-exclusion (temporary/permanent)
- kontrollü admin override (yüksek risk)

Bu build’de UI: `frontend/src/pages/ResponsibleGaming.jsx`.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner / Compliance
- Support (read-only) (varsa)

---

## 3) Temel akış (UI’daki implementasyona göre)

### 3.1 Oyuncu bulma
1) Player email gir.
2) Search.

> Not: UI içinde bu lookup’ın mocked / implement değil olabileceğine dair yorumlar var.

### 3.2 RG aksiyonu uygulama
1) Action seç:
   - cooloff
   - exclude_temp / exclude_perm
   - lift (dangerous)
2) Reason gir.
3) Apply Action.

**API çağrıları (UI’ın kullandığı):**
- `POST /api/v1/rg/admin/override/{player_id}`

---

## 4) Operasyon notları

- RG closed-loop olmalı:
  - aksiyon → audit kanıtı → player tarafında doğrulama
- Jurisdiction onay gerektiriyorsa “lift” için Approval Queue kullan.

---

## 5) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Search hep demo profil döndürüyor.
   - **Muhtemel neden:** UI mocked.
   - **Çözüm:** email ile admin player search endpoint’i implement et.
   - **Doğrulama:** gerçek player profili gelir.

2) **Belirti:** Apply Action 404.
   - **Muhtemel neden:** `/api/v1/rg/admin/override/{player_id}` yok veya route uyuşmuyor.
   - **Çözüm:** doğru RG override route’u implement/wire et.
   - **Doğrulama:** POST 200.

3) **Belirti:** Apply Action 422.
   - **Muhtemel neden:** backend farklı payload alanları bekliyor (`lift_exclusion` vs `action`).
   - **Çözüm:** UI payload’ını backend schema ile hizala.
   - **Doğrulama:** request kabul.

4) **Belirti:** Apply Action 400 “Reason required”.
   - **Muhtemel neden:** backend reason zorunlu.
   - **Çözüm:** reason boş olmamalı.
   - **Doğrulama:** action success.

5) **Belirti:** Lift başarılı ama player hâlâ excluded.
   - **Muhtemel neden:** player status update yok veya cache.
   - **Çözüm:** player status “active” olmalı; Logs ile doğrula.
   - **Doğrulama:** player login olur ve bloklanmaz.

6) **Belirti:** Self-exclusion endpoint’leri tutarsız.
   - **Muhtemel neden:** `rg.py` ve `rg_player.py` içinde duplike route’lar.
   - **Çözüm:** route’ları konsolide et; datetime’ı timezone-aware yap.
   - **Doğrulama:** tutarlı response contract.

7) **Belirti:** RG endpoint’lerinde 401/403.
   - **Muhtemel neden:** auth/permission.
   - **Çözüm:** tekrar login; owner role.
   - **Doğrulama:** endpoint 200.

8) **Belirti:** RG aksiyonları için audit kanıtı yok.
   - **Muhtemel neden:** sadece bazı aksiyonlar audited.
   - **Çözüm:** tüm admin override’ları Audit Log’a yaz.
   - **Doğrulama:** Audit Log `RG_ADMIN_OVERRIDE` içerir.

9) **Belirti:** Policy onay gerektiriyor ama lift tek kişiyle yapılıyor.
   - **Muhtemel neden:** approval enforcement yok.
   - **Çözüm:** Approval Queue entegrasyonu veya lift’i kapat.
   - **Doğrulama:** lift için approval kaydı zorunlu.

---

## 6) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI `action` + `reason` gönderiyor, backend override farklı payload bekliyor.
   - **Muhtemel neden:** `backend/app/routes/rg.py` `require_reason` ile payload’ı `{ lift_exclusion: true }` gibi bekler.
   - **Etki:** UI RG aksiyonlarını güvenilir şekilde uygulayamaz.
   - **Admin workaround:** yok.
   - **Escalation paketi:** 422 body; payload mapping.
   - **Resolution owner:** Backend/Frontend

2) **Belirti:** Player email lookup mocked.
   - **Muhtemel neden:** admin player search endpoint yok.
   - **Etki:** RG aksiyonları doğru hedeflenemez.
   - **Resolution owner:** Backend

---

## 7) Doğrulama (UI + Logs + Audit + DB)

### 7.1 UI
- Success toast görünür.

### 7.2 System → Logs
- `/api/v1/rg/*` hataları var mı kontrol.

### 7.3 System → Audit Log
- Audit varsa `RG_ADMIN_OVERRIDE` doğrula.

### 7.4 DB doğrulama
- `player_rg_profile` güncellenir.

---

## 8) Güvenlik notları + rollback

- Exclusion kaldırma yüksek risk.
- Rollback:
  - exclusion’u tekrar uygula
  - policy gerekiyorsa approval request aç

---

## 9) İlgili linkler

- Approval Queue: `/docs/new/tr/admin/risk-compliance/approval-queue.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
