# Break-glass (EN) — Runbook

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Security  

Break-glass is the controlled procedure to recover administrative control when normal access is unavailable.

---

## 0) When to use

Use break-glass only for:
- No platform owner (super admin) can log in
- All admins are locked out / deleted
- Critical production incident where immediate mitigation is required and standard paths are blocked

Do **not** use break-glass for convenience.

---

## 1) Approvals and controls

Minimum controls (recommended):
- Two-person approval (Ops + Security/Engineering)
- Time-bounded access window
- Mandatory incident ticket reference

Record:
- who approved
- reason
- start/end timestamps
- exact actions executed

---

## 2) Procedure

### 2.1 Identify the required outcome
Pick exactly one:
- A) Create the first Platform Owner admin
- B) Reset password for an existing admin
- C) Re-enable a disabled admin

### 2.2 Execute (DB-level, last resort)

> Implementation varies by deployment. Use your internal DB access method (bastion/VPN).

General rule:
- Prefer **minimal changes** that restore normal access.
- Never delete system tenant.

### 2.3 Revoke break-glass access
- Remove temporary credentials
- Remove temporary network access
- Rotate secrets if exposure is suspected

---

## 3) Evidence (audit-ready)

### 3.1 UI evidence
- System → Audit Log export (time window)

### 3.2 Backend logs
- Capture relevant backend log lines (include `request_id` if available)

### 3.3 Database evidence
- Snapshot the changed rows (before/after) for:
  - `adminuser`
  - `tenant` (if touched)

---

## 4) Rollback / recovery

- If a wrong user was created or wrong tenant was modified: immediately disable the admin and produce an incident report.
- If credentials might have leaked: rotate affected secrets.

---

## 5) Post-mortem checklist

- [ ] Root cause documented
- [ ] Audit evidence produced
- [ ] Permissions reviewed
- [ ] Preventative fix backlog item created

