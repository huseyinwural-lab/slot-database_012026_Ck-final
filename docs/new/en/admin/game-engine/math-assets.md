# Math Assets (EN)

**Menu path (UI):** Game Engine → Math Assets  
**Frontend route:** `/math-assets`  
**Feature flag (UI):** `can_use_game_robot`  

---

## Ops Checklist (read first)

- Math Assets are the heavy math data used by Robots (paytables, reelsets).
- Upload/replace operations are production-impacting:
  - require a **reason** (backend enforces it)
  - must be traceable in **Audit Log**
- Before enabling a robot that references a new asset:
  - verify asset exists
  - verify JSON is valid

---

## 1) Purpose and scope

Math Assets stores math data referenced by robots:
- `paytable` assets
- `reelset` assets

Frontend: `frontend/src/pages/MathAssetsPage.jsx`.
Backend: `backend/app/routes/math_assets.py`.

---

## 2) Who uses this / permission requirements

- Game Engine / Math Ops

Access:
- UI gated by `can_use_game_robot`.
- Backend requires admin auth.

---

## 3) What you can do (UI)

- Search assets by ref key
- Filter by type (paytable/reelset)
- View JSON content
- Upload new asset (JSON)

> Note: UI currently implements upload (POST) but not replace flow.

---

## 4) Core workflows

### 4.1 List/search assets
1) Open Game Engine → Math Assets.
2) Search by ref key.
3) Filter by type.

**API calls (UI):**
- `GET /api/v1/math-assets?search=<text>&type=<paytable|reelset|all>`

Expected response:
- `{ items: MathAsset[], meta: { total, page, page_size } }`

### 4.2 View asset content
1) Click Eye.
2) Inspect JSON.

### 4.3 Upload a new asset
1) Click **Upload New Asset**.
2) Fill:
   - ref_key (unique)
   - type (paytable/reelset)
   - JSON content
3) Upload.

**API calls:**
- `POST /api/v1/math-assets`

**Body (as per UI):**
- `{ ref_key, type, content }`

**Backend requirement:**
- requires audit reason via `X-Reason` header or `reason` field.

**Audit event (expected):**
- `MATH_ASSET_UPLOAD`

### 4.4 Replace an existing asset (backend capability)
Backend supports replace.

**API calls:**
- `POST /api/v1/math-assets/{asset_id}/replace`

**Reason requirement:**
- backend requires `X-Reason` header for replace.

---

## 5) Field guide (practical tips)

- Use versioned ref keys: `basic_pay_v1`, `basic_pay_v2`.
- Prefer creating a new ref key over replacing in-place unless you have strict rollback.
- Validate JSON schema offline before upload.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Assets list empty.
   - **Likely cause:** no assets exist or tenant mismatch.
   - **Fix:** seed assets; confirm tenant context.
   - **Verification:** GET returns items.

2) **Symptom:** Upload fails with “Invalid JSON content”.
   - **Likely cause:** invalid JSON in UI form.
   - **Fix:** validate JSON.
   - **Verification:** upload proceeds.

3) **Symptom:** Upload fails with 400 REASON_REQUIRED.
   - **Likely cause:** backend requires reason, UI does not send one.
   - **Fix:** add reason field in UI or set `X-Reason` header.
   - **Verification:** POST returns 200.

4) **Symptom:** Upload returns 409 conflict.
   - **Likely cause:** ref_key already exists.
   - **Fix:** use new ref_key or use replace.
   - **Verification:** upload succeeds.

5) **Symptom:** Upload returns 400 “Missing required fields”.
   - **Likely cause:** missing ref_key/type/content.
   - **Fix:** fill required fields.
   - **Verification:** POST accepted.

6) **Symptom:** Replace fails with 400 REASON_REQUIRED.
   - **Likely cause:** replace requires `X-Reason` header.
   - **Fix:** provide header.
   - **Verification:** replace succeeds.

7) **Symptom:** Robot references asset ref_key but simulation fails.
   - **Likely cause:** asset content schema invalid.
   - **Fix:** validate schema; upload corrected version.
   - **Verification:** simulation works.

8) **Symptom:** No audit trail for asset changes.
   - **Likely cause:** audit log not visible or not persisted.
   - **Fix:** confirm Audit Log route; ensure audit.log_event is called.
   - **Verification:** `MATH_ASSET_UPLOAD`/`MATH_ASSET_REPLACE` visible.

9) **Symptom:** Upload succeeds but UI list doesn’t refresh.
   - **Likely cause:** client state not updated.
   - **Fix:** refresh; verify GET.
   - **Verification:** asset appears.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI does not send audit reason, but backend requires it.
   - **Likely Cause:** backend reads `X-Reason`/`reason` and raises REASON_REQUIRED.
   - **Impact:** upload/replace may fail.
   - **Admin Workaround:** none.
   - **Escalation Package:** capture 400 response.
   - **Resolution Owner:** Frontend/Backend

2) **Symptom:** UI lacks replace workflow though backend supports it.
   - **Likely Cause:** UI missing Replace button.
   - **Impact:** operators must use new ref keys; cannot hotfix an asset easily.
   - **Resolution Owner:** Frontend/Product

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Upload shows success toast.
- Asset appears in list.

### 8.2 System → Logs
- Search `/api/v1/math-assets` 4xx/5xx.

### 8.3 System → Audit Log
- Filter: `MATH_ASSET_UPLOAD`, `MATH_ASSET_REPLACE`.

### 8.4 DB verification
- `mathasset` rows created/updated.

---

## 9) Security notes + rollback

- Math assets define payout behavior indirectly.
- Rollback options:
  - revert robot binding to previous asset ref_key
  - or replace asset content with previous version (requires strict change control)

---

## 10) Related links

- Robots: `/docs/new/en/admin/game-engine/robots.md`
- Simulator: `/docs/new/en/admin/system/simulator.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
