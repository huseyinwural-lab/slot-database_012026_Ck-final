# Common Errors (EN)

This guide standardizes **platform-wide** errors that appear across multiple admin menus.

**Scope boundary:**
- This file includes only recurring, cross-menu errors where operators need a consistent first-response playbook.
- Menu-specific edge cases remain on the menu page; link back here when relevant.

---

## 1) Admin login — Network Error

- **Symptoms (UI):** Login button spins; “Network Error”; no token stored.
- **Likely Causes:**
  - backend base URL misconfigured
  - `/api` routing mismatch in ingress
  - CORS blocked
  - TLS / mixed-content blocked
  - auth endpoint returning 5xx
- **Fix Steps:**
  1) Verify frontend uses `REACT_APP_BACKEND_URL` and calls `/api/*` endpoints.
  2) In DevTools → Network, capture the failing request and status.
  3) Confirm the request URL matches environment (preview/stage/prod).
  4) Check backend health/version endpoint: `GET /api/v1/version`.
  5) If CORS/mixed-content, fix origin/TLS configuration.
- **Verification (UI + Logs + Audit + DB):**
  - UI: Login succeeds and redirects; token stored.
  - Logs: backend shows 200 on `/api/auth/login` (or equivalent).
  - Audit Log: (optional) login events if implemented.
  - DB: user exists and is active.
- **Escalation Package:**
  - `POST /api/auth/login` → status + response body
  - Browser console error + network HAR snippet
  - Log keywords: `CORS`, `origin`, `auth`, `login`, `request_id`
- **Related Pages:**
  - `/docs/new/en/runbooks/break-glass.md`
  - `/docs/new/en/runbooks/password-reset.md`

---

## 2) 401 Unauthorized (token missing/expired)

- **Symptoms (UI):** Redirect to login; toast “Unauthorized”; API calls fail.
- **Likely Causes:**
  - token missing
  - token expired
  - Authorization header not sent
  - clock skew
- **Fix Steps:**
  1) Re-login and reproduce.
  2) Verify `Authorization: Bearer <token>` is present.
  3) Clear storage and login again.
  4) Check backend token TTL and clock.
- **Verification (UI + Logs + Audit + DB):**
  - UI: page loads without redirect.
  - Logs: 200 responses after re-auth.
  - Audit Log: (optional) auth failures tracked.
  - DB: admin user role active.
- **Escalation Package:**
  - failing endpoint + status 401
  - Log keywords: `jwt`, `expired`, `authorization`
- **Related Pages:**
  - `/docs/new/en/admin/system/admin-users.md`

---

## 3) 403 Forbidden (role/scope/tenant context)

- **Symptoms (UI):** “Forbidden”; menu hidden; actions blocked.
- **Likely Causes:**
  - role missing required permission
  - feature/capability not enabled
  - owner-only enforced
  - wrong tenant context
- **Fix Steps:**
  1) Confirm which role is logged in.
  2) Confirm the menu is owner-only or feature-gated.
  3) Switch to platform owner for verification.
  4) Validate tenant context header/selection.
- **Verification (UI + Logs + Audit + DB):**
  - UI: access works with correct role.
  - Logs: 200 for same endpoint as owner.
  - Audit Log: permission changes recorded (if implemented).
  - DB: role/capabilities set.
- **Escalation Package:**
  - endpoint + status 403
  - Log keywords: `permission`, `forbidden`, `ownerOnly`, `tenant_id`
- **Related Pages:**
  - `/docs/new/en/admin/roles-permissions.md`

---

## 4) 404 Not Found (UI → Backend route gap)

- **Symptoms (UI):** Empty tab; toast “Not found”; Network shows 404.
- **Likely Causes:**
  - backend route not implemented
  - wrong API prefix (`/api` missing)
  - version mismatch (`/v1` vs `/v2`)
- **Fix Steps:**
  1) Capture the exact failing path from DevTools.
  2) Search backend routes for the path.
  3) Confirm ingress requires `/api` prefix.
  4) Add gap entry to backend gap register.
- **Verification (UI + Logs + Audit + DB):**
  - UI: tab loads.
  - Logs: 200 response for route.
  - Audit Log: (if mutation) audit events exist.
  - DB: objects exist.
- **Escalation Package:**
  - failing method/path + 404
  - Log keywords: `404`, `Not Found`, route name
- **Related Pages:**
  - `/docs/new/en/runbooks/backend-gap-register.md`

---

## 5) 422 Validation failed (form/import)

- **Symptoms (UI):** Form submit fails; validation toast; API returns 422.
- **Likely Causes:**
  - schema mismatch (field name/type)
  - required field missing
  - invalid enum value
- **Fix Steps:**
  1) Inspect 422 response body details.
  2) Compare UI payload with backend schema.
  3) Fix field naming/type.
  4) Add UI validation where missing.
- **Verification (UI + Logs + Audit + DB):**
  - UI: submit succeeds.
  - Logs: 200/201.
  - Audit Log: mutation event exists.
  - DB: record created/updated.
- **Escalation Package:**
  - method/path + 422 + response detail
  - Log keywords: `validation`, `pydantic`, `422`
- **Related Pages:**
  - `/docs/new/en/admin/system/api-keys.md`

---

## 6) 500 Internal Server Error

- **Symptoms (UI):** Generic error toast; request returns 500.
- **Likely Causes:**
  - unhandled exception
  - DB connection issues
  - null/None handling bug
  - serialization error
- **Fix Steps:**
  1) Capture request_id.
  2) Locate stack trace in backend logs.
  3) Identify the failing route and payload.
  4) Fix root cause; add test.
- **Verification (UI + Logs + Audit + DB):**
  - UI: action succeeds.
  - Logs: no exception; 200 responses.
  - Audit Log: action success logged.
  - DB: state consistent.
- **Escalation Package:**
  - failing method/path + request_id
  - Log keywords: `Traceback`, `Exception`, `request_id`
- **Related Pages:**
  - `/docs/new/en/admin/system/logs.md`

---

## 7) Timeout / Gateway timeout (upstream/provider)

- **Symptoms (UI):** spinner never ends; 504/timeout.
- **Likely Causes:**
  - upstream provider slow
  - long-running query
  - background job blocked
- **Fix Steps:**
  1) Re-run with smaller filters/time window.
  2) Check backend logs for slow queries.
  3) Verify provider status.
  4) Add timeouts + retries appropriately.
- **Verification (UI + Logs + Audit + DB):**
  - UI: request returns within SLA.
  - Logs: latency improved.
  - Audit Log: (if mutation) event recorded.
  - DB: no partial writes.
- **Escalation Package:**
  - method/path + timing + status
  - Log keywords: `timeout`, `gateway`, `latency`
- **Related Pages:**
  - `/docs/new/en/guides/performance-guardrails.md`

---

## 8) CORS / mixed content

- **Symptoms (UI):** Console shows CORS errors; blocked requests.
- **Likely Causes:**
  - backend missing CORS origins
  - http/https mismatch
- **Fix Steps:**
  1) Confirm frontend is served over HTTPS.
  2) Ensure backend URL is HTTPS.
  3) Add allowed origins in backend.
  4) Re-deploy and test.
- **Verification (UI + Logs + Audit + DB):**
  - UI: requests succeed.
  - Logs: requests hit backend.
  - Audit Log: n/a.
  - DB: n/a.
- **Escalation Package:**
  - console error snippet
  - failing URL
  - Log keywords: `CORS`, `origin`, `blocked`
- **Related Pages:**
  - `/docs/new/en/guides/deployment.md`

---

## 9) Stale cache / propagation delay (visibility/flags/games)

---

## 10) Export CSV no-op (no request / no download)

- **Symptoms (UI):** Click “Export CSV” and nothing happens; no download.
- **Likely Causes:**
  - FE: button has no `onClick` or handler throws and gets swallowed
  - FE: missing `responseType: 'blob'` so browser can’t download
  - BE: export endpoint missing (404) or wrong path (`/v1` vs `/api/v1`)
- **Fix Steps:**
  1) DevTools → Network (All) with “Preserve log”: click export.
     - If **no request**: FE handler wiring issue.
     - If request **404/5xx**: backend route gap.
  2) FE: call export with `responseType: 'blob'` and trigger download via `URL.createObjectURL(blob)` + `<a download>`.
  3) BE: return `text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="..."`.
- **Verification:**
  - Network shows 200 on export endpoint.
  - Browser downloads a `.csv` file.

- **Symptoms (UI):** change saved but UI still old; list not updated.
- **Likely Causes:**
  - cache TTL
  - async pipeline delay
  - multi-service propagation
- **Fix Steps:**
  1) Hard refresh.
  2) Re-fetch endpoint.
  3) Check caches/invalidation logic.
  4) Verify with Logs.
- **Verification (UI + Logs + Audit + DB):**
  - UI: new state visible.
  - Logs: cache invalidation logged.
  - Audit Log: change recorded.
  - DB: record updated.
- **Escalation Package:**
  - method/path + timestamps
  - Log keywords: `cache`, `invalidate`, `ttl`
- **Related Pages:**
  - `/docs/new/en/admin/system/feature-flags.md`

---

## 10) Feature flag no-op / not persisted

- **Symptoms (UI):** toggle looks successful but resets after refresh.
- **Likely Causes:**
  - safe stub backend
  - missing persistence
  - tenant scope mismatch
- **Fix Steps:**
  1) Toggle and refresh.
  2) Validate GET vs POST behavior.
  3) Check backend implementation.
  4) Escalate as persistence gap.
- **Verification (UI + Logs + Audit + DB):**
  - UI: toggle persists.
  - Logs: state saved.
  - Audit Log: toggle event exists.
  - DB: flag record updated.
- **Escalation Package:**
  - endpoints: `/api/v1/flags/*`
  - Log keywords: `flags`, `toggle`, `persist`
- **Related Pages:**
  - `/docs/new/en/admin/system/feature-flags.md`

---

## 11) Tenant context mismatch (wrong tenant ops)

- **Symptoms (UI):** changes appear in wrong tenant; lists empty.
- **Likely Causes:**
  - wrong tenant selected
  - missing tenant header
  - tenant_id not applied in queries
- **Fix Steps:**
  1) Confirm selected tenant.
  2) Verify tenant header in Network.
  3) Check backend query filters.
  4) Retest.
- **Verification (UI + Logs + Audit + DB):**
  - UI: correct tenant data appears.
  - Logs: tenant_id matches.
  - Audit Log: tenant_id correct.
  - DB: changes scoped.
- **Escalation Package:**
  - method/path + observed tenant_id
  - Log keywords: `tenant_id`, `scope`
- **Related Pages:**
  - `/docs/new/en/admin/system/tenants.md`

---

## 12) Pagination/filter mismatch (empty list but exists)

- **Symptoms (UI):** UI list says empty; DB has data.
- **Likely Causes:**
  - backend ignores query params
  - wrong default filters
  - off-by-one pagination
- **Fix Steps:**
  1) Remove filters and retry.
  2) Check request query params.
  3) Validate backend respects params.
  4) Fix pagination.
- **Verification (UI + Logs + Audit + DB):**
  - UI: list shows items.
  - Logs: params handled.
  - Audit Log: n/a.
  - DB: n/a.
- **Escalation Package:**
  - request URL with params
  - Log keywords: `page`, `limit`, `filter`
- **Related Pages:**
  - `/docs/new/en/admin/system/reports.md`

---

## 13) Import job stuck / job status not updating

- **Symptoms (UI):** import in-progress forever; no status updates.
- **Likely Causes:**
  - worker not running
  - job state not persisted
  - polling endpoint missing
- **Fix Steps:**
  1) Capture job_id.
  2) Check job status endpoint.
  3) Verify worker/queue.
  4) Restart worker if needed.
- **Verification (UI + Logs + Audit + DB):**
  - UI: status transitions to done/failed.
  - Logs: job processed.
  - Audit Log: import events.
  - DB: job row updated.
- **Escalation Package:**
  - method/path + job_id
  - Log keywords: `import`, `job`, `worker`, `queue`
- **Related Pages:**
  - `/docs/new/en/admin/core/games.md`

---

## 14) Report empty / timezone mismatch

- **Symptoms (UI):** report shows 0 but finance expects data.
- **Likely Causes:**
  - timezone mismatch
  - wrong date window
  - aggregation delay
- **Fix Steps:**
  1) Confirm timezone expectations.
  2) Expand date window.
  3) Compare against raw transactions.
  4) Fix timezone normalization.
- **Verification (UI + Logs + Audit + DB):**
  - UI: counts match.
  - Logs: aggregation job ran.
  - Audit Log: export logged.
  - DB: transactions present.
- **Escalation Package:**
  - report query + timezone
  - Log keywords: `timezone`, `aggregation`, `report`
- **Related Pages:**
  - `/docs/new/en/admin/system/reports.md`

---

## 15) Withdrawals stuck / approval queue backlog

- **Symptoms (UI):** withdrawals pending; queue grows.
- **Likely Causes:**
  - approval workflow not processing
  - external payout provider issues
  - risk holds
- **Fix Steps:**
  1) Check Approval Queue.
  2) Check payout provider status.
  3) Check Logs for payout errors.
  4) Use Kill Switch if abuse wave.
- **Verification (UI + Logs + Audit + DB):**
  - UI: withdrawal transitions.
  - Logs: payout succeeds.
  - Audit Log: approval recorded.
  - DB: withdrawal status updated.
- **Escalation Package:**
  - withdrawal_id + endpoints
  - Log keywords: `withdrawal`, `payout`, `provider`, `approval`
- **Related Pages:**
  - `/docs/new/en/admin/core/withdrawals.md`
  - `/docs/new/en/admin/risk-compliance/approval-queue.md`

---

## 16) KYC document processing issues (unreadable/duplicate)

- **Symptoms (UI):** document unreadable; duplicates; review fails.
- **Likely Causes:**
  - corrupted uploads
  - duplicate doc ids
  - OCR/extraction failure
- **Fix Steps:**
  1) Request re-upload.
  2) Validate document storage link.
  3) Deduplicate by hash.
  4) Re-run processing.
- **Verification (UI + Logs + Audit + DB):**
  - UI: document renders.
  - Logs: processing success.
  - Audit Log: review recorded.
  - DB: doc row consistent.
- **Escalation Package:**
  - doc_id + endpoint
  - Log keywords: `kyc`, `document`, `ocr`, `duplicate`
- **Related Pages:**
  - `/docs/new/en/admin/operations/kyc-verification.md`

---

## 17) Lockfile / yarn drift (CI)

- **Symptoms (UI/CI):** preview deploy blocked; CI fails on lint/install.
- **Likely Causes:**
  - yarn.lock differs between branches
  - dependency version mismatch
- **Fix Steps:**
  1) Use yarn (not npm).
  2) Ensure lockfile is committed.
  3) Re-run CI.
  4) If needed, regenerate lockfile consistently.
- **Verification (UI + Logs + Audit + DB):**
  - UI: preview deployment succeeds.
  - Logs: CI shows green.
  - Audit Log: n/a.
  - DB: n/a.
- **Escalation Package:**
  - CI job link + error log
  - keywords: `yarn.lock`, `install`, `eslint`
- **Related Pages:**
  - `/docs/new/en/guides/deployment.md`

---

## 18) Migrations / head mismatch

- **Symptoms (UI/API):** 500 errors after deploy; migrations fail.
- **Likely Causes:**
  - missing migration
  - wrong head revision
  - environment drift
- **Fix Steps:**
  1) Check migration status.
  2) Identify current head.
  3) Apply missing migrations.
  4) Re-deploy.
- **Verification (UI + Logs + Audit + DB):**
  - UI: endpoints recover.
  - Logs: migration applied.
  - Audit Log: n/a.
  - DB: schema matches head.
- **Escalation Package:**
  - migration tool output
  - keywords: `alembic`, `head`, `revision`, `migration`
- **Related Pages:**
  - `/docs/new/en/guides/migrations.md`
