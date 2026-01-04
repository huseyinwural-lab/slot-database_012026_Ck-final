# Şifre Sıfırlama (TR) — Runbook

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Security  

Bu runbook, Admin kullanıcılar için (ve varsa Player için) **şifre sıfırlama prosedürünü** deterministik şekilde tanımlar.

> Bu bir operasyonel prosedürdür (runbook). UI menü sayfaları adımları tekrar etmeden buraya link vermelidir.

---

## 0) Kapsam

### Dahil
- Admin şifre sıfırlama (mevcut implementasyon)
- Kanıt/doğrulama kaynakları (log/audit)
- “Hiç admin yok” senaryosu için break-glass referansı

### Hariç
- Email gönderimi / SMTP provider entegrasyonu (bu codebase’te yok)

---

## 1) Admin şifre sıfırlama — mevcut codebase davranışı

### 1.1 Endpoint’ler
- Reset token üret:
  - `POST /api/v1/auth/request-password-reset`
  - Body: `{ "email": "admin@example.com" }`
- Reset’i doğrula (yeni şifreyi uygula):
  - `POST /api/v1/auth/reset-password`
  - Body: `{ "token": "...", "new_password": "..." }`

### 1.2 Önemli notlar
- Şu an **email gönderimi yok**.
- Reset token backend log’larına yazdırılıyor (dev/test için uygun, prod için riskli).
- Token expiry: ~30 dakika (JWT).

### 1.3 Prosedür (adım adım)
1) Token üretimini tetikle
   - Admin email ile `POST /api/v1/auth/request-password-reset` çağır.
   - Beklenen cevap: generic success mesajı (user enumeration engeli).

2) Token’ı backend log’undan bul
   - Backend/container log’larında şunu ara:
     - `[Password Reset] Token for` (sabit prefix)
     - admin email
   - Token’ı kopyala.

3) Şifreyi sıfırla
   - `POST /api/v1/auth/reset-password` çağır:
     - `token` (log’dan)
     - `new_password`
   - Beklenen: success JSON.

4) Doğrula
   - `POST /api/v1/auth/login` ile login dene.
   - Gerekli menülere erişimi doğrula.

---

## 2) Kanıt & doğrulama (UI + Log + DB)

### 2.1 UI (tercih edilen)
- System → Audit Log
  - Zaman aralığı ve actor’a göre filtrele
  - Not: Implementasyona göre password reset audit’e düşmeyebilir.

### 2.2 Backend / container log
- Arama anahtarları:
  - admin email
  - `[Password Reset] Token for` (token yazdırma)
  - `x-request-id` (response header’dan alındıysa)

### 2.3 Database (hard evidence gerekiyorsa)
- Tablo: `adminuser`
  - `password_reset_token` reset tamamlanana kadar token ile eşleşir.
  - Reset sonrası `password_hash` değişir.

---

## 3) Hata senaryoları ve çözümler

1) **Belirti:** Log’larda token bulunamıyor
   - Olası neden: yanlış environment / yanlış log kaynağı
   - Çözüm: doğru backend instance log’larına bak; request adımını tekrar çalıştır.

2) **Belirti:** `RESET_TOKEN_INVALID` / token mismatch
   - Olası neden: token expire veya daha yeni token eskisini overwrite etti
   - Çözüm: request adımını yeniden çalıştır; en yeni token’ı kullan.

3) **Belirti:** Reset başarılı ama login hâlâ başarısız
   - Olası neden: admin disabled (`is_active=false` veya `status!=active`)
   - Çözüm: Admin Users ekranından admin’i aktif et veya break-glass change control ile DB’den düzelt.

---

## 4) Break-glass (hiç admin yoksa)

DB’de admin yoksa veya herkes lockout olduysa break-glass sürecini uygula:
- `/docs/new/tr/runbooks/break-glass.md`
