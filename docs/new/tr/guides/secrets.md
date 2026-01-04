# Konfigürasyon & Secrets Yönetimi (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Platform Engineering / Security  

Bu rehber, ortamlar arası konfigürasyon ve secret yönetiminin nasıl yapılacağını tanımlar.

---

## 1) Prensipler

1) **Git içinde secret olmaz**
2) **Log içinde secret olmaz**
3) **Ortam bazlı ayrım** (dev/staging/prod)
4) **Güvenli rotation** (blast radius + rollback dokümante)

---

## 2) Konfigürasyon vs secrets

- **Konfigürasyon**: hassas olmayan ayarlar (feature flag, limit, URL)
- **Secrets**: credential ve signing key’ler

Secret örnekleri:
- DB password
- JWT secret / signing key
- webhook signing secret’ları
- payment provider API key’leri

---

## 3) Secret’lar nerede tutulmalı?

Ortam başına tek “source of truth” seç:

- **Kubernetes**: Secrets / ExternalSecrets (önerilen)
- **CI/CD**: GitHub Actions Secrets (build/deploy için)
- **Vault**: merkezi secret store

Kural:
- `.env` dosyaları **sadece local** içindir.

---

## 4) Rotation playbook (minimum)

### 4.1 JWT secret rotation

Adımlar:
1) Yeni key ekle (destekliyorsa dual-read, single-write)
2) Deploy
3) TTL / session expiry bekle
4) Eski key’i kaldır

Dual-key yoksa:
- bakım penceresinde rotate et
- kullanıcıları re-login zorla

### 4.2 Webhook secret rotation

Adımlar:
1) Provider dashboard’da yeni secret set et
2) Backend secret’ını güncelle
3) Deploy
4) Test webhook delivery ile doğrula

---

## 5) CI/CD

- CI secret basmamalı
- masked variable kullan
- mümkünse short-lived credential

---

## 6) Runtime değiştirilebilir config

Tercih:
- env var ile yönetilen konfigürasyon
- veya tenant bazlı DB feature flag

Legacy:
- `/docs/ops/log_schema.md` (redaction)
- `/docs/payments/*` (provider secrets)
