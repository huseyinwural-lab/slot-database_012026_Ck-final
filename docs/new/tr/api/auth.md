# Auth API (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Backend Engineering  

---

## Admin login

- `POST /api/v1/auth/login`

Beklenen kullanım:
- Frontend `{ email, password }` gönderir.
- Response token / admin identity payload döner.

Rate limit:
- Login endpoint’i rate limit middleware ile korunur.
- Bkz: `backend/app/middleware/rate_limit.py`

---

## Şifre sıfırlama

- `POST /api/v1/auth/request-password-reset`
- `POST /api/v1/auth/reset-password`

Önemli:
- Mevcut kod reset token’ı log’a basar (dev için uygun).
- Prod’da email delivery provider kullanılmalıdır.

Bkz:
- `/docs/new/tr/runbooks/password-reset.md`
