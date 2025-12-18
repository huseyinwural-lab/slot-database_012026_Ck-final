# CSP Policy (Admin/Tenant UI) (P4.3)

Scope:
- Primary: **admin + tenant UIs**
- Player UI: evaluate separately (3rd party scripts more likely)

Principles:
- Start with **CSP Report-Only**.
- Do not enforce until you have **≥ 7 days** of violation data.
- Long-term: **no inline**.
- Short-term: allow a transition path via **nonce** or temporary `unsafe-inline`.

---

## 1) Canonical starting policy (safe-by-default, low break risk)

This is the recommended baseline policy for admin/tenant UI.

```text
default-src 'self';
base-uri 'self';
object-src 'none';
frame-ancestors 'none';

script-src 'self' 'report-sample';
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
font-src 'self' data:;
connect-src 'self' https: wss:;

# optional (if you embed iframes in the future):
# frame-src 'self';
```

Notes:
- `style-src 'unsafe-inline'` is often needed initially for React apps and component libraries; aim to remove later.
- `script-src` starts strict: no `unsafe-inline` by default.
- `connect-src` includes `https:` and `wss:` for APIs/websockets across domains.

---

## 2) Known allowances (expand via report-only data)

Add only what you observe and approve.

Common additions:
- CDN for static assets (if used):
  - `script-src https://cdn.example.com`
  - `style-src https://cdn.example.com`
  - `img-src https://cdn.example.com`
- Analytics / tag manager (admin UI only):
  - `script-src https://www.googletagmanager.com`
  - `connect-src https://www.google-analytics.com`
- Font providers:
  - `font-src https://fonts.gstatic.com`
  - `style-src https://fonts.googleapis.com`

---

## 3) Report-only collection

### Option A (preferred): report endpoint
If you have an endpoint to collect reports, configure CSP with `report-to` or `report-uri`.

- `report-to` is the modern mechanism (requires a `Report-To` header).
- `report-uri` is legacy but still widely supported.

If you don't have a report collector yet:

### Option B (fallback): manual collection
- Browser DevTools Console will show CSP violations.
- Collect:
  - failing directive (`script-src`, `connect-src`, ...)
  - blocked URL
  - affected page
- Use this data to update allowlists.

---

## 4) Transition path to "no inline"

### Option 1: Nonce-based scripts (recommended)
- Set `script-src 'self' 'nonce-<random>'`.
- Add nonce attribute to inline scripts.

### Option 2: Temporary `unsafe-inline` (last resort, time-boxed)
- If you must, temporarily add:
  - `script-src 'self' 'unsafe-inline'`
- Only during the transition period, and remove during the Tighten phase.

---

## 5) Operator validations

Check headers:
```bash
curl -I https://<admin-domain>/
curl -I https://<admin-domain>/tenants
```

Expected:
- During report-only phase: `Content-Security-Policy-Report-Only` present
- During enforce phase: `Content-Security-Policy` present

UI smoke (admin/tenant):
- login
- tenants list
- settings pages
- logout

