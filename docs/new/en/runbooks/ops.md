# Ops Runbook (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops  

This is an ops-oriented summary. Deep procedures live under legacy `/docs/ops/`.

---

## 1) Backup

Baseline:
- take daily logical backups
- verify restore regularly

Legacy:
- `/docs/ops/backup.md`
- `/docs/ops/cron/casino-backup.example`

---

## 2) Restore / DR

Default strategy:
- restore-from-backup

Legacy:
- `/docs/ops/dr_runbook.md`
- `/docs/ops/restore_drill_proof/template.md`

---

## 3) Retention & purge

Guidance:
- define retention windows (example: 14 days for backups)
- avoid destructive operations without audit

---

## 4) Operational evidence

For any P0/P1:
- capture `request_id`
- capture tenant id
- capture git SHA
