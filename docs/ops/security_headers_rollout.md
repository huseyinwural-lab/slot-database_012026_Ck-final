# CSP + HSTS Rollout Plan (P4.3)

Goal: increase security **without breaking prod**.

Non-negotiables:
- CSP starts **Report-Only**.
- Collect **≥ 7 days** of violation data before enforcing.
- HSTS ramps gradually.
- Rollback must be possible in **< 5 minutes** via a single config switch.
- Scope priority: admin/tenant UIs. Player UI evaluated separately.

Canonical policy reference:
- `docs/ops/csp_policy.md`

Canonical Nginx include design (rollback lever):
- `docs/ops/snippets/security_headers.conf`
- `docs/ops/snippets/security_headers_report_only.conf`
- `docs/ops/snippets/security_headers_enforce.conf`

---

## Phase 0 — Baseline headers (if not already present)

### Change
Enable baseline headers:
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `X-Frame-Options: DENY` (defense-in-depth)

(Already included in both snippets.)

### Validate
```bash
curl -I https://<admin-domain>/
```
Expected: headers present.

### Rollback (< 5 min)
- Switch include to OFF (comment out include in `security_headers.conf`) and reload nginx.

---

## Phase 1 — CSP Report-Only (ADMIN/TENANT)

### Change
Use report-only include:
- `security_headers_report_only.conf` sets `Content-Security-Policy-Report-Only`.

### Validate
1) Header present:
```bash
curl -I https://<admin-domain>/ | grep -i content-security-policy
```
Expected:
- `Content-Security-Policy-Report-Only: ...`

2) UI smoke:
- login
- tenants list
- settings pages
- logout

3) Collect violations for **≥ 7 days**:
- preferred: report endpoint (if configured)
- fallback: browser console collection

### Rollback (< 5 min)
- Switch include to OFF (comment out include) and reload nginx.

---

## Phase 2 — CSP Enforce

### Gate (must satisfy)
- Report-only enabled for **≥ 7 days**
- Violations reviewed
- Allowlist updated in policy

### Change
Switch include to enforce:
- `security_headers_enforce.conf` sets `Content-Security-Policy`.

### Validate
```bash
curl -I https://<admin-domain>/ | grep -i content-security-policy
```
Expected:
- `Content-Security-Policy: ...`

UI smoke + monitor error rates.

### Rollback (< 5 min)
- Switch include back to `security_headers_report_only.conf`.

---

## Phase 3 — Tighten

### Change
Remove temporary allowances time-boxed during rollout:
- remove `script-src 'unsafe-inline'` (if it was added)
- reduce `connect-src` to concrete allowlist if desired
- remove unnecessary host allowances

### Validate
- Same as Phase 2

### Rollback (< 5 min)
- Revert to previous known-good CSP config include.

---

## Phase 4 — HSTS (staging)

### Change
Enable low max-age on staging only:
- `max-age=300` (5 minutes)

In `security_headers_enforce.conf`:
```nginx
add_header Strict-Transport-Security "max-age=300" always;
```

### Validate
```bash
curl -I https://<staging-admin-domain>/ | grep -i strict-transport-security
```
Expected:
- `Strict-Transport-Security: max-age=300`

### Rollback (< 5 min)
- Comment out the HSTS line and reload nginx.

---

## Phase 5 — HSTS (prod ramp)

### Change (ramp)
Start low and increase over time:
- Day 1: `max-age=300`
- Day 2: `max-age=3600`
- Day 3: `max-age=86400`
- Week 2+: `max-age=31536000`

**Default stance:**
- `includeSubDomains`: NO (until validated)
- `preload`: NO (until you are ready for a long-lived commitment)

### Validate
```bash
curl -I https://<prod-admin-domain>/ | grep -i strict-transport-security
```
Expected:
- header exists, correct max-age

### Rollback (< 5 min)
- Remove/disable the HSTS line and reload.

> Note: browsers may cache HSTS for the duration of max-age. This is why we ramp slowly.

---

## Break-glass procedure (single-switch)

If CSP/HSTS breaks login or critical pages:
1) Switch `security_headers.conf` include to OFF or report-only.
2) Reload nginx.
3) Confirm headers via `curl -I`.
4) Re-run UI smoke.
