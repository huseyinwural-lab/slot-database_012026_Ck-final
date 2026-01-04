# CMS (EN)

**Menu path (UI):** System → CMS  
**Frontend route:** `/cms`  
**Owner-only:** Yes (menu config)

---

## Ops Checklist (read first)

- Confirm tenant context even if CMS is platform-like. Some CMS items may be tenant-scoped.
- For publish/unpublish flows: keep evidence in **Audit Log** + **Logs** (if implemented).
- Use CMS for controlled content updates; do not treat it as a support channel.

---

## 1) Purpose and scope

CMS provides admin capabilities to manage content pages (e.g., Terms, Privacy, FAQ, landing content) displayed to players.

In this build, CMS UI is implemented in `frontend/src/pages/CMSManagement.jsx`.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin)
- Potentially Content Manager role (if implemented)

> UI visibility: System → CMS is owner-only in `frontend/src/config/menu.js`.

---

## 3) UI overview

CMS page includes:
- Content page list
- Create new page (title/slug/content)
- Edit existing page
- Delete page
- Basic status indicators

---

## 4) Core workflows (step-by-step)

### 4.1 List CMS pages
1) Open System → CMS.
2) Confirm existing pages render.

**API calls (backend):**
- `GET /api/v1/cms/pages`

### 4.2 Create a CMS page
1) Click **Create Page**.
2) Fill:
   - title
   - slug
   - content
3) Submit.

**API calls:**
- `POST /api/v1/cms/pages`

### 4.3 Edit a CMS page
1) Select a page.
2) Update content.
3) Save.

**API calls:**
- `PUT /api/v1/cms/pages/{page_id}`

### 4.4 Delete a CMS page
1) Select a page.
2) Click delete.
3) Confirm.

**API calls:**
- `DELETE /api/v1/cms/pages/{page_id}`

---

## 5) Operational notes

- Use strict review and approvals for player-facing legal pages.
- Prefer small, reversible changes.
- Maintain a change log externally if Audit Log is not implemented for CMS.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** CMS page list is empty.
   - **Likely cause:** no pages exist yet.
   - **Fix:** create a test page.
   - **Verification:** page appears in list.

2) **Symptom:** CMS list fetch fails with 401.
   - **Likely cause:** admin session expired.
   - **Fix:** re-login.
   - **Verification:** GET returns 200.

3) **Symptom:** CMS list fetch fails with 403.
   - **Likely cause:** role lacks permissions.
   - **Fix:** use platform owner; implement role entitlements.
   - **Verification:** role can access CMS.

4) **Symptom:** Create page fails with 409 / slug conflict.
   - **Likely cause:** slug must be unique.
   - **Fix:** change slug.
   - **Verification:** create returns 201.

5) **Symptom:** Create/edit fails with 422.
   - **Likely cause:** missing required fields (title/slug/content).
   - **Fix:** validate UI fields.
   - **Verification:** request passes.

6) **Symptom:** Edit does not persist after refresh.
   - **Likely cause:** PUT endpoint not implemented or commit failing.
   - **Fix:** verify `PUT /api/v1/cms/pages/{id}` exists and commits.
   - **Verification:** refresh shows updated content.

7) **Symptom:** Delete fails with 404.
   - **Likely cause:** page id not found.
   - **Fix:** refresh list; retry.
   - **Verification:** list reflects deletion.

8) **Symptom:** CMS page renders in UI but broken on player site.
   - **Likely cause:** player site routes not wired to CMS content.
   - **Fix:** verify public CMS consumption endpoints/SSR logic.
   - **Verification:** player site displays content.

9) **Symptom:** Audit evidence missing for CMS changes.
   - **Likely cause:** CMS routes not audited.
   - **Fix:** add auditing or record change tickets.
   - **Verification:** Audit Log shows `cms.page.created/updated/deleted`.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** CMS works but has no approvals / publish workflow.
   - **Likely cause:** MVP CRUD only.
   - **Impact:** risk of unreviewed legal content updates.
   - **Admin Workaround:** run manual approval process (2-person review).
   - **Escalation Package:** product requirement for approvals/publish states.
   - **Resolution Owner:** Product/Backend
   - **Verification:** publish status + audit trail exist.

2) **Symptom:** CMS endpoints exist but are not tenant-scoped.
   - **Likely cause:** missing tenant_id on cms_page model.
   - **Impact:** cross-tenant content leakage.
   - **Admin Workaround:** treat CMS as platform-global until scoped.
   - **Escalation Package:** confirm data model requirements.
   - **Resolution Owner:** Backend
   - **Verification:** pages are filtered by tenant context.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- List loads.
- Create/update/delete reflect without stale state.

### 8.2 System → Logs
- Error Logs show no 4xx/5xx for cms endpoints.

### 8.3 System → Audit Log
- CMS changes produce audit events (if implemented).

### 8.4 DB verification
- `cms_pages` table has expected rows.

---

## 9) Security notes + rollback

- CMS changes are player-facing; treat as production changes.
- Rollback strategy:
  - revert page content to last known good
  - or delete new page

---

## 10) Related links

- Logs: `/docs/new/en/admin/system/logs.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
