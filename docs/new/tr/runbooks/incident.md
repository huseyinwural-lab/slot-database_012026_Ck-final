# Incident & Destek Runbook (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops  

Bu runbook, incident response akışını ve eskalasyon sınırlarını tanımlar.

---

## 1) Seviyelendirme

- **P0**: tam kesinti, para hareketi blok, data integrity riski
- **P1**: ciddi bozulma, kısmi kesinti
- **P2**: kritik olmayan bug
- **P3**: küçük issue

---

## 2) İlk müdahale checklist (tüm seviyeler)

1) Scope’u doğrula (tek tenant mı, çok tenant mı)
2) request_id ve zaman damgalarını al
3) son deploy SHA’yı doğrula
4) backend log ve audit trail kontrol et

---

## 3) Triage hızlı harita

### Auth/login
- frontend request URL doğrula
- backend `/api/v1/auth/login` hata kontrol
- rate limit ihtimali

### Payments/webhook
- webhook failure playbook
- signature secret doğrulama

### Payouts
- polling hata/timeout
- provider bağlantısı

Legacy:
- `/docs/ops/webhook-failure-playbook.md`
- `/docs/ops/log_schema.md`

---

## 4) Rollback vs hotfix

Rollback:
- integrity riski
- payment/payout bozuk
- migration fail

Hotfix:
- izole değişiklik
- doğrulanmış fix

DR:
- `/docs/ops/dr_runbook.md`

---

## 5) Eskalasyon

Eskalasyon:
- **DBA**: migration/lock/replication
- **Security**: credential compromise şüphesi
- **Payments**: provider failure / reconciliation
