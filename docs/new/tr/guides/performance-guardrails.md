# Performans & Koruma Önlemleri (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Platform Engineering  

Bu doküman, sistemin yük altında öngörülebilir davranması için pratik guardrail’leri tanımlar.

---

## 1) Rate limiting

Backend kritik endpoint’ler için basit in-memory rate limiter içerir.

Referans:
- `backend/app/middleware/rate_limit.py`

Not:
- dev/local/test/ci ortamlarında limitler gevşektir
- prod/staging daha sıkıdır (örn login)

Uyarı:
- in-memory limiter node-local çalışır; multi-node için shared limiter (Redis/gateway) gerekir.

---

## 2) Yüksek maliyetli operasyonlar

Örnekler:
- tenant purge / destructive cleanup
- büyük backfill’ler
- toplu user operasyonları

Öneri:
- platform owner yetkisi zorunlu
- background job olarak çalıştır
- progress ve audit event üret

---

## 3) Background job’lar

Deploy’ınıza göre dokümante edin:
- scheduler/worker
- queue backend
- retry policy
- dead-letter stratejisi

---

## 4) Büyük tenant’lar

Ops notları:
- payout status geçişleri daha uzun sürebilir
- bounded polling + retry tercih et
- ağır migration’lar için bakım penceresi planla
