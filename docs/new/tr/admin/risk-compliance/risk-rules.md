# Risk Rules (TR)

**Menü yolu (UI):** Risk & Compliance → Risk Rules  
**Frontend route:** `/risk`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Kural oluşturma/aktif etme öncesi **tenant context**’i doğrula.
- Her değişiklikte şu kanıtları topla:
  - failing request URL + status code (DevTools → Network)
  - mümkünse **Audit Log** kaydı
  - runtime sorunları için **Logs**
- Kuralları prod etkili kabul et; rollback planı olmadan değiştirme.

---

## 1) Amaç ve kapsam

Risk Rules, risk skoru ve fraud tespiti için otomatik kural setini yönetir. Tipik olarak:
- risk skoruna etki eder
- case/alert üretir
- aksiyonları gate eder (withdrawal payout, bonus, RTP change)

Bu build’de UI: `frontend/src/pages/RiskManagement.jsx` (Rules tab).

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin) / Risk Ops
- Fraud / Compliance analistleri (rol sistemi varsa)

> Menü görünürlüğü: `frontend/src/config/menu.js` bu menüyü owner-only yapar.

---

## 3) Alt başlıklar / tab’lar (UI)

`RiskManagement.jsx` çok tab’lı bir “Risk & Fraud Engine” ekranıdır:
- Overview (dashboard)
- Live Alerts
- Cases
- Investigation (evidence/notes)
- Rules
- Velocity
- (UI-only) Payment / IP & Geo / Bonus Abuse / Logic

Bu sayfa ağırlıklı olarak **Rules**’u dokümante eder.

---

## 4) Temel akışlar (adım adım)

### 4.1 Rule listesi
1) Risk & Compliance → Risk Rules aç.
2) **Rules** tab’ına geç.

**API çağrıları (UI’ın kullandıkları):**
- `GET /api/v1/risk/rules`

### 4.2 Rule oluşturma
1) **Add Rule** tıkla.
2) Doldur:
   - name
   - category (`account` / `payment` / `bonus_abuse`)
   - severity
   - score_impact
3) **Save Rule**.

**API çağrıları:**
- `POST /api/v1/risk/rules`

### 4.3 Rule enable/disable (toggle)
1) Rules tablosunda **Activate/Pause** tıkla.

**API çağrıları:**
- `POST /api/v1/risk/rules/{id}/toggle`

---

## 5) Saha rehberi (pratik ipuçları)

- Az ama yüksek-sinyalli kuralları tercih et.
- Kademeli rollout:
  - önce observe-only (varsa)
  - sonra enforcement
- Değişiklik gerekçesi + rollback koşulunu mutlaka not al.

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Risk Rules açılıyor ama Rules tab’ı boş.
   - **Muhtemel neden:** tenant için henüz rule yok.
   - **Çözüm:** rule oluştur; tenant context’i kontrol et.
   - **Doğrulama:** GET liste döner.

2) **Belirti:** Rules tab 401.
   - **Muhtemel neden:** session süresi doldu.
   - **Çözüm:** tekrar login.
   - **Doğrulama:** GET 200.

3) **Belirti:** Rules tab 403.
   - **Muhtemel neden:** user owner değil.
   - **Çözüm:** owner admin ile dene.
   - **Doğrulama:** endpoint 200.

4) **Belirti:** Rule create 404.
   - **Muhtemel neden:** `POST /api/v1/risk/rules` implement değil.
   - **Çözüm:** backend route ekle veya UI’da create’i kapat.
   - **Doğrulama:** POST 201 ve list güncellenir.

5) **Belirti:** Toggle 404.
   - **Muhtemel neden:** `POST /api/v1/risk/rules/{id}/toggle` implement değil.
   - **Çözüm:** toggle route ekle.
   - **Doğrulama:** status değişir ve refresh sonrası kalır.

6) **Belirti:** Create 422.
   - **Muhtemel neden:** request schema/type uyuşmuyor.
   - **Çözüm:** body alanlarını hizala (`score_impact` numeric).
   - **Doğrulama:** POST kabul.

7) **Belirti:** Rule değişiyor ama sahada etkisi yok.
   - **Muhtemel neden:** enforcement pipeline yok/bağlı değil.
   - **Çözüm:** Logs’ta rule evaluation araması; entegrasyonu doğrula.
   - **Doğrulama:** condition oluşunca alert/case davranışı değişir.

8) **Belirti:** Rule değişikliği için audit kanıtı yok.
   - **Muhtemel neden:** risk endpoint’leri audited değil.
   - **Çözüm:** audit ekle; geçici olarak change ticket ile kanıt tut.
   - **Doğrulama:** **Audit Log**’da `risk.rule.*` event’leri görünür.

9) **Belirti:** Payment/Geo/Bonus gibi tab’lar var ama veri gelmiyor.
   - **Muhtemel neden:** ilgili backend endpoint’leri eksik.
   - **Çözüm:** gap olarak dokümante et; endpoint’leri implement et.
   - **Doğrulama:** tab’lar veri gösterir.

---

## 7) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI birçok risk endpoint’i çağırıyor; backend sadece `GET /api/v1/risk/rules` sağlıyor.
   - **Muhtemel neden:** `backend/app/routes/risk.py` bu build’de sadece `GET /rules` içeriyor.
   - **Etki:** Risk Engine tab’larının çoğu (dashboard/alerts/cases/velocity/blacklist/evidence) çalışmaz.
   - **Admin workaround:** Yok. Incident triage için Logs’a pivot.
   - **Escalation paketi:**
     - UI’ın çağırdığı beklenen endpoint’ler:
       - `GET /api/v1/risk/dashboard`
       - `GET /api/v1/risk/alerts`
       - `GET /api/v1/risk/cases`
       - `PUT /api/v1/risk/cases/{id}/status`
       - `GET /api/v1/risk/velocity`
       - `GET/POST /api/v1/risk/blacklist`
       - `GET/POST /api/v1/risk/evidence`
     - Anahtar kelime: `risk/`
   - **Resolution owner:** Backend
   - **Doğrulama:** endpoint’ler 200 döner; UI tab’lar dolar.

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Rule listede görünür.
- Toggle refresh sonrası kalıcıdır.

### 8.2 System → Logs
- `/api/v1/risk/*` için 4xx/5xx var mı Error Logs’ta bak.

### 8.3 System → Audit Log
- Rule create/toggle event’leri görünmeli (audit varsa).

### 8.4 DB doğrulama
- Tenant için `risk_rules` satırları oluşur.

---

## 9) Güvenlik notları + rollback

- Kurallar finansal aksiyonları etkileyebilir.
- Rollback:
  - son rule’u disable et
  - semptom durdu mu doğrula
  - kanıt paketi üret (Logs + Audit Log)

---

## 10) İlgili linkler

- Approval Queue: `/docs/new/tr/admin/risk-compliance/approval-queue.md`
- Fraud Check: `/docs/new/tr/admin/risk-compliance/fraud-check.md`
- Responsible Gaming: `/docs/new/tr/admin/risk-compliance/responsible-gaming.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
