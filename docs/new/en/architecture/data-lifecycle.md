# Data Lifecycle (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Security  

This document describes how data should be treated over time, especially for audit and finance.

---

## 1) Soft delete vs hard delete

- Soft delete: keep record, mark inactive/deleted
- Hard delete: remove record

Recommendation:
- prefer soft delete for auditability in finance contexts

---

## 2) Retention

Define:
- log retention
- audit retention
- backup retention

Legacy:
- `/docs/ops/backup.md`

---

## 3) Purge

Purge should be:
- owner-only
- logged to audit
- reversible only via restore

---

## 4) Tenant delete impact

Before implementing tenant delete:
- enumerate tenant-scoped tables
- define what is preserved (audit/ledger)
- define deletion policy
