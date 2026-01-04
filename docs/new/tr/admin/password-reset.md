# Admin Şifre Sıfırlama (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Security  

Bu doküman, mevcut codebase’te admin şifre sıfırlama davranışını ve prod için önerilen yaklaşımı açıklar.

---

## Mevcut implementasyon (codebase davranışı)

Endpoint’ler:
- `POST /api/v1/auth/request-password-reset` (email)
- `POST /api/v1/auth/reset-password` (token + new_password)

Önemli:
- Şu an **email gönderimi yok**.
- Reset token backend log’a yazdırılıyor (dev için uygun, prod için riskli).

Operasyon akışı:
1) Admin email için `request-password-reset` çağır
2) Backend log’dan token’ı al
3) Token ile `reset-password` çağır

---

## Break-glass kurtarma (DB’de hiç admin yoksa)

`adminuser` tablosu boşsa ilk Platform Owner (süper admin) DB üzerinden oluşturulur.

Prod önerisi:
- Sabit şifre (örn `Admin123!`) kullanma.
- Şifreyi env/secret yönetiminden üret.
- Break-glass işlemlerini audit’le.
