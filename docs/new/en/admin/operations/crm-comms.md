# CRM & Comms (EN)

**Menu path (UI):** Operations → CRM & Comms  
**Frontend route:** `/crm`  
**Feature flag (UI):** `can_use_crm`  

---

## Ops Checklist (read first)

- Validate tenant context; comms can be customer-facing and regulated.
- For any send:
  - keep a change record (campaign id + segment + template)
  - validate in **Logs** and **Audit Log** (if implemented)
- If module is disabled:
  - check Operations → Kill Switch state for `crm`
  - confirm `can_use_crm` capability.

---

## 1) Purpose and scope

CRM & Comms manages outbound communications:
- campaigns
- message templates
- player segments
- channels/providers

Frontend: `frontend/src/pages/CRM.jsx`.

Backend: `/api/v1/crm/*` exists, but several routes are stubs returning empty arrays.

---

## 2) Who uses this / permission requirements

- CRM Ops / Retention
- Compliance (review)

Access:
- UI gated by `can_use_crm`
- Backend enforces module access via `enforce_module_access(..., module_key="crm")`

---

## 3) Sub-sections / tabs (UI)

CRM.jsx tabs:
- Campaigns
- Templates
- Segments
- Channels

---

## 4) Core workflows

### 4.1 View campaigns
**API calls:**
- `GET /api/v1/crm/campaigns`

### 4.2 Create a campaign (draft)
1) Click **New Campaign**.
2) Fill:
   - name
   - channel (email/sms/push)
   - segment_id (mock id)
   - template_id (mock id)
3) Create.

**API calls:**
- `POST /api/v1/crm/campaigns`

### 4.3 Send a campaign
1) In Campaigns table, click **Send**.

**API calls:**
- `POST /api/v1/crm/campaigns/{campaign_id}/send`

### 4.4 View templates / segments / channels
**API calls:**
- `GET /api/v1/crm/templates`
- `GET /api/v1/crm/segments`
- `GET /api/v1/crm/channels`

---

## 5) Operational notes

- Always run compliance review for:
  - bonuses / VIP offers
  - jurisdictional restrictions
  - unsubscribe requirements
- Prefer dry-run mode for new segments (if implemented).

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** CRM menu not visible.
   - **Likely cause:** `can_use_crm` not enabled.
   - **Fix:** grant feature.
   - **Verification:** menu appears.

2) **Symptom:** CRM shows “Coming soon / Not implemented”.
   - **Likely cause:** backend returns 404 for one or more tabs.
   - **Fix:** implement missing endpoint(s) or disable tab.
   - **Verification:** tab loads data.

3) **Symptom:** Campaign list always empty.
   - **Likely cause:** backend stub returns `[]`.
   - **Fix:** implement persistence.
   - **Verification:** created campaigns appear.

4) **Symptom:** Create campaign returns 403.
   - **Likely cause:** module access blocked by kill switch or missing entitlement.
   - **Fix:** check Kill Switch for `crm`; confirm capability.
   - **Verification:** POST returns 200/201.

5) **Symptom:** Send campaign returns 500.
   - **Likely cause:** provider integration not configured.
   - **Fix:** configure provider (email/sms/push); inspect Logs.
   - **Verification:** send queued.

6) **Symptom:** Send returns 200 but no messages delivered.
   - **Likely cause:** async job not implemented.
   - **Fix:** implement queue worker and delivery logs.
   - **Verification:** delivery receipts logged.

7) **Symptom:** Segment selection is confusing.
   - **Likely cause:** UI uses mock ids and segments endpoint returns empty.
   - **Fix:** implement real segmentation model.
   - **Verification:** segments are selectable.

8) **Symptom:** No audit evidence for campaign sends.
   - **Likely cause:** CRM routes are not audited.
   - **Fix:** add audit events for create/send.
   - **Verification:** Audit Log shows `crm.campaign.sent`.

9) **Symptom:** Unsubscribe compliance not met.
   - **Likely cause:** no opt-out enforcement.
   - **Fix:** enforce opt-out list; include unsubscribe link.
   - **Verification:** opt-out honored.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Templates/Segments/Channels endpoints exist but always return empty arrays.
   - **Likely Cause:** `backend/app/routes/crm.py` implements stubs returning `[]`.
   - **Impact:** UI tabs populate with empty lists; CRM is not production-grade.
   - **Admin Workaround:** maintain templates/segments externally.
   - **Escalation Package:** define data models + persistence.
   - **Resolution Owner:** Backend

2) **Symptom:** Sending does not integrate with real providers.
   - **Likely Cause:** no email/sms/push integration.
   - **Impact:** campaign sends do not reach customers.
   - **Resolution Owner:** Backend/Product

---

## 8) Verification (UI + Logs + Audit)

### 8.1 UI
- Campaign create shows success.
- Send shows queued.

### 8.2 System → Logs
- Search for `/api/v1/crm/*` 4xx/5xx.

### 8.3 System → Audit Log
- Verify create/send events (if implemented).

---

## 9) Security notes

- Treat CRM content as regulated.
- Avoid logging raw message bodies.

---

## 10) Related links

- Kill Switch: `/docs/new/en/admin/operations/kill-switch.md`
- Support: `/docs/new/en/admin/operations/support.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
