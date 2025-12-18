# CSP + HSTS Checklist (03:00 Operator) (P4.3)

Canonical references:
- Policy: `docs/ops/csp_policy.md`
- Rollout plan: `docs/ops/security_headers_rollout.md`
- Nginx snippets:
  - `docs/ops/snippets/security_headers.conf`
  - `docs/ops/snippets/security_headers_report_only.conf`
  - `docs/ops/snippets/security_headers_enforce.conf`

---

## STG-SecHeaders-01 (staging enablement)

Kubernetes UI-nginx wiring assumption:
- ConfigMap mounted into frontend-admin nginx:
  - `k8s/frontend-admin-security-headers-configmap.yaml`
- Rollback lever (single switch):
  - `SECURITY_HEADERS_MODE=off|report-only|enforce`



Change:
- Set: `SECURITY_HEADERS_MODE=report-only`

Validate (headers):
```bash
export STAGING_DOMAIN="<fill-me>"
curl -I "https://${STAGING_DOMAIN}/" | egrep -i "content-security-policy|strict-transport-security"
```
Expected:
- `Content-Security-Policy-Report-Only` exists
- `Strict-Transport-Security` exists (low max-age)

Validate (UI):
- Login
- Tenants
- Settings
- Logout

Collect violations:
- Keep report-only for **≥ 7 days**
- Capture blocked URLs + directives (console or report endpoint)

Rollback (< 5 min):
- Set: `SECURITY_HEADERS_MODE=off` and redeploy/restart the frontend-admin pod.

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
- Set: `SECURITY_HEADERS_MODE=enforce`

Validate:
```bash
curl -I https://<admin-domain>/ | grep -i content-security-policy
```
Expected:
- `Content-Security-Policy` exists

UI smoke + monitor error rates.

Rollback (< 5 min):
- Set: `SECURITY_HEADERS_MODE=report-only` and redeploy/restart the frontend-admin pod.

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

Default (this task):
- HSTS is already enabled in `SECURITY_HEADERS_MODE=report-only` with:
  - `max-age=300`
  - no includeSubDomains
  - no preload

Validate:
```bash
export STAGING_DOMAIN="<fill-me>"
curl -I "https://${STAGING_DOMAIN}/" | grep -i strict-transport-security
```

Rollback (< 5 min):
- Set: `SECURITY_HEADERS_MODE=off` and redeploy/restart the frontend-admin pod.

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

