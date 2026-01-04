# Release Runbook (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Release Engineering / Ops  

Bu runbook, deterministik bir release sürecini ve release gate kapanışı için gereken minimum kanıt paketini tanımlar.

---

## 1) Hedef

- Güvenli yayın
- Şu sorulara net cevap: **ne çalışıyor, ne değişti, nasıl doğrulandı**
- Rollback kararının hızlı ve kayıtlı olması

---

## 2) Pre-release checklist

### 2.1 Code & CI

- `frontend-lint.yml` **PASS**
- Acceptance workflow (compose) **PASS**
- E2E smoke (money loop) **PASS**

Tek mesaj rapor şablonu:

```text
frontend_lint PASS/FAIL
prod_compose_acceptance PASS/FAIL
release-smoke-money-loop PASS/FAIL
```

### 2.2 Konfigürasyon & secrets

- Prod secret’lar secret manager’da mevcut
- Webhook secret’ları konfigüre
- JWT secret’ları konfigüre
- Kod içinde hardcoded URL/port yok

---

## 3) Deploy prosedürü (üst seviye)

1) Hedef ortamı doğrula (staging/prod)
2) Uygulama image’larını deploy et
3) Gerekliyse DB migration çalıştır
4) Smoke check’leri koş

Minimum smoke check:
- Admin login çalışıyor
- Tenant scope doğru çözülüyor
- Payment webhook verification açık

---

## 4) Kanıt paketi (zorunlu)

Her release için en az şunlar:

1) Deploy edilen **Git SHA**
2) CI sonuç linkleri / ekran görüntüleri
3) DB migration durumu (çıktı/log)
4) Smoke test notu (ne test edildi)
5) Kullanılan manuel override’lar (break-glass, tenant impersonation)

---

## 5) Rollback karar ağacı

Rollback tercih et:
- data integrity riski
- payments/payouts etkilenmişse
- auth/login bozuksa
- migration fail olduysa veya tutarsız state ürettiyse

Hotfix tercih et:
- değişiklik izoleyse
- doğrulanmış fix hazırsa
- rollback daha büyük risk yaratacaksa

---

## 6) Post-release izleme

İlk 30–60 dakika:
- 5xx hata oranı
- webhook failure
- payout status geçişleri

Structured log alanları:
- `request_id`
- `tenant_id`

Legacy:
- `/docs/ops/log_schema.md`
- `/docs/ops/dr_runbook.md`
