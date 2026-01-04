# Release Runbook (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Release Engineering / Ops  

This runbook defines a deterministic release process and the minimum evidence required to close a release gate.

---

## 1) Goals

- Ship safely
- Be able to answer: **what is running, what changed, how verified**
- Ensure rollback decision is quick and documented

---

## 2) Pre-release checklist

### 2.1 Code & CI

- `frontend-lint.yml` is **PASS**
- Acceptance workflow (compose) is **PASS**
- E2E smoke (money loop) is **PASS**

Report template (single message):

```text
frontend_lint PASS/FAIL
prod_compose_acceptance PASS/FAIL
release-smoke-money-loop PASS/FAIL
```

### 2.2 Configuration & secrets

- Prod secrets are present in secret manager
- Webhook secrets configured
- JWT secrets configured
- No hardcoded URLs/ports in code

---

## 3) Deploy procedure (high-level)

1) Confirm target environment (staging/prod)
2) Deploy application image(s)
3) Run DB migrations (if required)
4) Run smoke checks

Smoke checks (minimum):
- Admin login works
- Tenant scope resolves correctly
- Payment webhook verification enabled

---

## 4) Evidence pack (required)

Attach the following for each release:

1) **Git SHA** deployed
2) CI results links / screenshots
3) DB migration status (output/log)
4) Smoke test notes (what was tested)
5) Any manual overrides used (break-glass, tenant impersonation)

---

## 5) Rollback decision tree

Use rollback when:
- data integrity risk
- payments/payouts impacted
- auth/login broken
- migrations failed or produced inconsistent state

Prefer hotfix when:
- change is isolated
- verified fix exists
- rollback would cause larger risk than patch

---

## 6) Post-release monitoring

First 30–60 minutes:
- watch error rates (5xx)
- watch webhook failures
- watch payout status transitions

Use structured logging fields:
- `request_id`
- `tenant_id`

Legacy references:
- `/docs/ops/log_schema.md`
- `/docs/ops/dr_runbook.md`
