# Ops Runbook (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops  

Bu doküman, ops odaklı bir özet sunar. Derin prosedürler legacy `/docs/ops/` altındadır.

---

## 1) Backup

Baseline:
- günlük logical backup
- düzenli restore doğrulaması

Legacy:
- `/docs/ops/backup.md`
- `/docs/ops/cron/casino-backup.example`

---

## 2) Restore / DR

Default strateji:
- restore-from-backup

Legacy:
- `/docs/ops/dr_runbook.md`
- `/docs/ops/restore_drill_proof/template.md`

---

## 3) Retention & purge

Öneri:
- retention window tanımla (örn backup için 14 gün)
- audit olmadan destructive operasyon yapma

---

## 4) Operasyon kanıtı

Her P0/P1 için:
- `request_id`
- tenant id
- git SHA
