# API Keys (EN)

**Menu path (UI):** System → API Keys  
**Frontend route:** `/keys`  
**Owner-only:** Yes  

---

## 1) Purpose and scope

The API Keys menu manages scope-based API keys used for external integrations and internal automation (e.g., Game Robot). Keys are **security-critical** secrets.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin) only.
- Tenant admins should not access API key management.

---

## 3) Sub-sections / functional areas

In the current UI (`frontend/src/pages/APIKeysPage.jsx`):
- Key list
- Create key (dialog)
- Toggle active/inactive
- Scopes selection

---

## 4) Core workflows

### 4.1 View key list
1) Open System → API Keys.
2) Review existing keys:
   - Name
   - Key prefix
   - Tenant
   - Scopes
   - Status

**API calls (observed from frontend):**
- List: `GET /api/v1/api-keys/`
- Scope catalog: `GET /api/v1/api-keys/scopes`

### 4.2 Create a new API key
1) Click **New API Key**.
2) Enter **Name** (use a strict naming convention).
3) Select **Scopes** (least privilege).
4) Click **Create**.
5) Copy the generated secret.

**Important:** the secret is shown **once**.

**API calls (observed from frontend):**
- Create: `POST /api/v1/api-keys/` body `{ name, scopes }`

### 4.3 Rotate an API key (recommended procedure)
Rotation is an operational pattern (two keys in parallel) even if the UI does not provide a dedicated “rotate” button.

1) Create a **new key** with the same scopes.
2) Deploy / configure the integration to use the **new key**.
3) Validate successful requests.
4) Disable (or revoke) the old key.

### 4.4 Revoke / disable a key
In the current UI, disabling is performed via an “Active/Inactive” toggle.

**API calls (observed from frontend):**
- Toggle active: `PATCH /api/v1/api-keys/{id}` body `{ active: true|false }`

**Important implementation note:** in the current backend routes, a `PATCH /api/v1/api-keys/{id}` endpoint is not present. In this build, the UI may receive **404 Not Found** when toggling status.

---

## 5) Field guide (practical tips)

- Use a naming convention like: `<system>-<env>-<purpose>-<owner>-<date>`.
- Select the smallest possible set of scopes.
- Store key secrets in a secret manager (never in chat, tickets, or screenshots).
- During incidents, treat API keys as compromised until proven otherwise.

**Do not:**
- Reuse a production key in staging.
- Leave “temporary” keys active indefinitely.

---

## 6) Common errors (symptom → likely cause → fix → verification)

> Minimum 8 items (security/incident surface).

1) **Symptom:** 401 Unauthorized in an integration
   - Likely cause: wrong key, typo, missing `Authorization` header.
   - Fix: verify the integration uses the correct secret; re-copy from secret store.
   - Verification: backend logs show successful auth and requests return 200.

2) **Symptom:** 403 Forbidden
   - Likely cause: scope does not include the required permission.
   - Fix: create a new key with the correct scopes (least privilege).
   - Verification: request succeeds after switching to the new key.

3) **Symptom:** “Failed to load API key data” in UI
   - Likely cause: `/api/v1/api-keys/` call failed or tenant feature disabled.
   - Fix: confirm platform owner access; check Network response and error code.
   - Verification: key list loads and scopes list loads.

4) **Symptom:** “Failed to create API key”
   - Likely cause: missing name, no scope selected, invalid scope.
   - Fix: provide a name; select at least one scope; re-try.
   - Verification: create call returns success and secret is displayed once.

5) **Symptom:** Key created but secret was not copied
   - Likely cause: user closed dialog; secret only shown once.
   - Fix: create a new key and revoke the old one (do not attempt to retrieve secrets).
   - Verification: integration updated with new secret; old key is inactive.

6) **Symptom:** Toggle active/inactive returns 404
   - Likely cause: backend `PATCH /api/v1/api-keys/{id}` not implemented in this build.
   - Fix: confirm backend version supports key status updates; otherwise treat keys as “create-only” and rotate by creating new keys.
   - Verification: toggling works after backend is updated; or new key flow works end-to-end.

7) **Symptom:** Rotation breaks production integration
   - Likely cause: integration config still points to old key; deployment not applied.
   - Fix: ensure config change is deployed; temporarily re-enable old key if necessary.
   - Verification: successful requests observed and error rate drops.

8) **Symptom:** Suspected key leak
   - Likely cause: key shared in plain text, committed, or logged.
   - Fix: immediately disable/revoke the key; rotate secrets; follow incident process.
   - Verification: audit evidence + logs show key revoked and traffic blocked for the leaked key.

9) **Symptom:** Stage/prod mismatch
   - Likely cause: using staging key in prod or vice versa.
   - Fix: verify environment boundaries; keep separate keys and naming.
   - Verification: requests go to the correct environment and succeed.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Toggling a key Active/Inactive returns 404 Not Found.
   - **Likely Cause:** UI calls `PATCH /api/v1/api-keys/{id}` but this backend build does not expose a PATCH route for updating key status.
   - **Impact:** Admin cannot disable/revoke keys via UI toggle (security/incident response impact). Rotation must be handled as create-new + cutover.
   - **Admin Workaround:**
     - Create a new key with correct scopes.
     - Update integration config to use the new key.
     - Treat old keys as “cannot be disabled via UI” until backend supports status updates.
   - **Escalation Package:**
     - HTTP method + path: `PATCH /api/v1/api-keys/{id}`
     - Request sample: `{ "active": false }`
     - Expected vs actual: expected 200; actual 404
     - Logs keywords:
       - `api-keys`
       - `PATCH`
       - `404`
   - **Resolution Owner:** Backend
   - **Verification:** After fix, toggling Active/Inactive returns 200 and key status changes persist after refresh.

---

## 8) Verification (UI + Logs + Audit + DB)

1) Identify the failing integration endpoint and capture the error (401/403/5xx).
2) Confirm which key is in use (prefix if available).
3) Check scopes required vs scopes assigned.
4) Rotate (new key → deploy config → verify → disable old key).
5) Produce audit-ready evidence (what changed, when, by whom).

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- The newly created key appears in the list.
- Scopes displayed match the intended least-privilege set.

### 8.2 System → Logs
- Look for auth failures/timeouts around integration calls.

### 8.3 App / container logs
- Search keywords:
  - `api-key`
  - `Unauthorized` / `Forbidden`
  - scope validation errors

### 8.4 System → Audit Log
- Expected audit events (naming varies by implementation):
  - `api_key.created`
  - `api_key.revoked` / `api_key.disabled`

### 8.5 Database audit (if present)
- Canonical table: `apikey` / `api_key` (implementation-dependent).
- Evidence should show:
  - new row for created key
  - status changes for revoked/disabled keys (if supported)

---

## 9) Security notes + rollback

- Treat API keys as secrets with production blast radius.
- Rollback strategy:
  - If a rotation causes downtime: temporarily re-enable the previous key (if supported) while deploying corrected configuration.
  - After stabilization, rotate again and revoke compromised keys.

---

## 10) Related links

- Break-glass: `/docs/new/en/runbooks/break-glass.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
