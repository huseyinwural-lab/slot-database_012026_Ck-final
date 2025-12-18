# CSP + HSTS Checklist (03:00 Operator) (P4.3)

Canonical references:
- Policy: `docs/ops/csp_policy.md`
- Rollout plan: `docs/ops/security_headers_rollout.md`
- Nginx snippets:
  - `docs/ops/snippets/security_headers.conf`
  - `docs/ops/snippets/security_headers_report_only.conf`
  - `docs/ops/snippets/security_headers_enforce.conf`

---

## 1) Enable CSP Report-Only

Change:
- Enable include: `security_headers_report_only.conf`

Validate (headers):
```bash
curl -I https://<admin-domain>/ | grep -i content-security-policy
```
Expected:
- `Content-Security-Policy-Report-Only` exists

Validate (UI):
- Login
- Tenants
- Settings
- Logout

Collect violations:
- Keep report-only for **≥ 7 days**
- Capture blocked URLs + directives (console or report endpoint)

Rollback (< 5 min):
- Switch include OFF (comment out include) and reload nginx.

---

## 2) Update allowlist

Change:
- Add only observed/approved sources to policy (see `docs/ops/csp_policy.md`).

Validate:
- UI smoke + confirm violations reduced.

---

## 3) Switch to CSP Enforce

Gate:
- ≥ 7 days violation data
- allowlist updated

Change:
- Switch include: `security_headers_enforce.conf`

Validate:
```bash
curl -I https://<admin-domain>/ | grep -i content-security-policy
```
Expected:
- `Content-Security-Policy` exists

UI smoke + monitor error rates.

Rollback (< 5 min):
- Switch back to report-only include.

---

## 4) Tighten

Change:
- Remove temporary allowances (time-boxed), especially any `unsafe-inline` for scripts.

Validate:
- UI smoke + no new violations.

Rollback (< 5 min):
- Revert to previous known-good include/policy.

---

## 5) HSTS staging

Change:
- Enable `Strict-Transport-Security` on staging:
  - `max-age=300`

Validate:
```bash
curl -I https://<staging-admin-domain>/ | grep -i strict-transport-security
```

Rollback (< 5 min):
- Remove HSTS line and reload.

---

## 6) HSTS prod ramp

Change:
- Day 1: `max-age=300`
- Day 2: `max-age=3600`
- Day 3: `max-age=86400`
- Week 2+: `max-age=31536000`

Default stance:
- `includeSubDomains`: NO
- `preload`: NO

Validate:
```bash
curl -I https://<prod-admin-domain>/ | grep -i strict-transport-security
```

Rollback (< 5 min):
- Remove/disable HSTS line and reload.

