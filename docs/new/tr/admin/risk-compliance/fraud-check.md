# Fraud Check (TR)

**Menü yolu (UI):** Risk & Compliance → Fraud Check  
**Frontend route:** `/fraud`  
**Sadece owner:** Evet  

---

## Ops Checklist (read first)

- Fraud Check sonucunu **karar destek** olarak gör; nihai hüküm gibi kullanma.
- Kanıt topla:
  - request payload + response (DevTools → Network)
  - runtime hataları için **Logs**
  - takip aksiyonları için **Audit Log** (varsa)
- Prompt’a secret veya tam PII yapıştırma.

---

## 1) Amaç ve kapsam

Fraud Check, transaction benzeri bir payload gönderip risk değerlendirmesi almak için kullanılır.

Bu build’de UI: `frontend/src/pages/FraudCheck.jsx` ve ekranda “via OpenAI” ifadesi geçer.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin)
- Risk/Fraud ekibi (rol sistemi varsa)

---

## 3) Temel akış

### 3.1 Analiz çalıştırma
1) Fraud Check aç.
2) Doldur:
   - amount
   - merchant
   - customer email
   - IP address
3) **Check Risk Score** tıkla.

**API çağrıları (UI’ın kullandığı):**
- `POST /api/v1/fraud/analyze`

UI’ın render ettiği beklenen response alanları:
- `fraud_risk_score` (0.0–1.0)
- `is_fraudulent` (bool)
- `recommendations` (string)
- `risk_factors` (string array)
- `confidence_level` (0.0–1.0)

---

## 4) Saha rehberi (pratik ipuçları)

- Gerçekçi ama **hassas olmayan** test verisi kullan.
- Senaryo bazlı test:
  - yüksek amount + şüpheli email domain
  - high-risk IP blokları
- Model sonucunu case/review süreçlerini tetiklemek için sinyal olarak kullan.

---

## 5) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Analyze 404.
   - **Muhtemel neden:** `/api/v1/fraud/analyze` implement değil.
   - **Çözüm:** backend route ekle; veya feature’ı kapat.
   - **Doğrulama:** POST 200 + beklenen schema.

2) **Belirti:** Analyze 500.
   - **Muhtemel neden:** model/entegrasyon hatası.
   - **Çözüm:** key/config kontrol; Logs incele.
   - **Doğrulama:** stabil response.

3) **Belirti:** Analyze 422.
   - **Muhtemel neden:** request body contract uyuşmuyor.
   - **Çözüm:** payload shape’i backend schema ile hizala.
   - **Doğrulama:** request kabul.

4) **Belirti:** Analyze çalışıyor ama UI render’da çöküyor.
   - **Muhtemel neden:** response alanları eksik/yanlış tip (`risk_factors` array değil).
   - **Çözüm:** backend response normalizasyonu.
   - **Doğrulama:** sonuç kartı düzgün render.

5) **Belirti:** Risk score hep 0% veya 100%.
   - **Muhtemel neden:** stubbed backend / hardcoded response.
   - **Çözüm:** backend logic doğrula; test case ekle.
   - **Doğrulama:** input’a göre skor değişir.

6) **Belirti:** Analyze 401.
   - **Muhtemel neden:** session süresi doldu.
   - **Çözüm:** tekrar login.
   - **Doğrulama:** POST 200.

7) **Belirti:** Analyze 403.
   - **Muhtemel neden:** rol yetkisiz.
   - **Çözüm:** owner admin ile dene; entitlements uygula.
   - **Doğrulama:** rol davranışı tasarımla uyumlu.

8) **Belirti:** PII / güvenlik endişesi.
   - **Muhtemel neden:** prompt’ta hassas veri kullanımı.
   - **Çözüm:** redaction; erişimi kısıtla; log’larda hashed identifier.
   - **Doğrulama:** Logs/Audit hassas payload içermez.

9) **Belirti:** Analiz için audit kanıtı yok.
   - **Muhtemel neden:** analysis audited değil.
   - **Çözüm:** Audit Log’a `fraud.analysis.run` event’i ekle.
   - **Doğrulama:** Audit Log’da analiz kayıtları görünür.

---

## 6) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI `POST /api/v1/fraud/analyze` çağırıyor; backend sadece `GET /api/v1/fraud/` veriyor.
   - **Muhtemel neden:** `backend/app/routes/fraud_detection.py` stub.
   - **Etki:** Fraud Check UI çalışamaz.
   - **Admin workaround:** Yok.
   - **Escalation paketi:**
     - Method + path: `POST /api/v1/fraud/analyze`
     - Beklenen vs gerçek: analysis schema vs 404
     - Anahtar kelime: `fraud/analyze`
   - **Resolution owner:** Backend
   - **Doğrulama:** POST endpoint var ve beklenen alanları döner.

2) **Belirti:** UI “via OpenAI” diyor ama entegrasyon görünür değil.
   - **Muhtemel neden:** entegrasyon wiring eksik.
   - **Etki:** maliyet/latency/failure mode tahmin edilemez.
   - **Admin workaround:** implement gelene kadar unavailable kabul et.
   - **Escalation paketi:** fraud service implementasyonu + model seçimi.
   - **Resolution owner:** Backend/Platform
   - **Doğrulama:** entegrasyon + dokümanlar var.

---

## 7) Doğrulama (UI + Logs + Audit)

### 7.1 UI
- Sonuç kartı render olur ve alanlar görünür.

### 7.2 System → Logs
- `/api/v1/fraud/analyze` için 4xx/5xx var mı bak.

### 7.3 System → Audit Log
- Varsa `fraud.analysis.run` event’lerini doğrula.

---

## 8) Güvenlik notları

- Input’ları hassas kabul et; erişimi kısıtla.
- Logs/Audit içinde raw email/IP tutmaktan kaçın.

---

## 9) İlgili linkler

- Risk Rules: `/docs/new/tr/admin/risk-compliance/risk-rules.md`
- Approval Queue: `/docs/new/tr/admin/risk-compliance/approval-queue.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
