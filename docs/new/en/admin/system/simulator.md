# Simulator (EN)

**Menu path (UI):** System → Simulator  
**Frontend route:** `/simulator`  
**Owner-only:** No (feature-gated)  

---

## 1) Purpose and scope

Simulator (Simulation Lab) is used to create scenarios, run simulations, and review outcomes for controlled testing (game math, bonus impacts, risk scenarios, etc.).

> Safety rule: simulations must not impact real-money production flows.

---

## 2) Who uses this / permission requirements

- Platform Owner: typically allowed.
- Tenant admins: only if tenant feature `can_use_game_robot` is enabled.

Observed gating:
- UI menu requires `feature: can_use_game_robot`.
- Backend has a stub `/api/v1/simulator/` with feature check.

---

## 3) Sub-sections / tabs

In the current UI (`frontend/src/pages/SimulationLab.jsx`):
- Overview
- Game Math
- Portfolio (UI placeholder)
- Bonus
- Cohort/LTV (UI placeholder)
- Risk (UI placeholder)
- RG (UI placeholder)
- A/B Sandbox (UI placeholder)
- Scenario Builder (UI placeholder)
- Archive

Observed data endpoint:
- Runs list: `GET /api/v1/simulation-lab/runs`

**Important implementation note:** backend `routes/simulation_lab.py` is currently a stub, so `/api/v1/simulation-lab/*` endpoints may return **404 Not Found**.

---

## 4) Core workflows

### 4.1 Create / configure a scenario
1) Choose the relevant simulator tab (e.g., Game Math, Bonus).
2) Configure scenario inputs.
3) Save or keep as draft (implementation-dependent).

### 4.2 Run a simulation
1) Click the run action for the scenario.
2) Monitor status in Overview/Archive.

### 4.3 Review results
1) Open completed runs.
2) Interpret key metrics.

### 4.4 Cleanup / reset
- Delete drafts and old runs according to retention policy.

---

## 5) Field guide (practical tips)

- Always label scenarios with:
  - objective
  - assumptions
  - dataset/version
- Keep scenarios small for faster execution.
- Avoid using simulation tooling during peak incident response unless explicitly required.

**Do not use in prod to:**
- “validate” a change without a rollback plan.

---

## 6) Common errors (symptom → likely cause → fix → verification)

> Minimum 8 items.

1) **Symptom:** Simulation run fails immediately
   - Likely cause: missing required input/config.
   - Fix: complete required fields; re-run.
   - Verification: run status transitions from draft → running.

2) **Symptom:** Runs list does not load
   - Likely cause: `/api/v1/simulation-lab/runs` endpoint missing.
   - Fix: confirm backend supports Simulation Lab routes.
   - Verification: endpoint returns run array and UI renders.

3) **Symptom:** Results not visible after completion
   - Likely cause: UI cache or missing results payload.
   - Fix: refresh; check run details endpoint (if implemented).
   - Verification: results panels populate.

4) **Symptom:** Unexpected results
   - Likely cause: math asset mismatch; wrong dataset.
   - Fix: verify math asset versioning; rerun with correct inputs.
   - Verification: results align with expected baseline.

5) **Symptom:** Performance issues
   - Likely cause: scenario too large or backend worker limitations.
   - Fix: reduce scenario size; run off-peak.
   - Verification: runtime decreases and completes.

6) **Symptom:** 403 Forbidden
   - Likely cause: tenant feature `can_use_game_robot` disabled.
   - Fix: enable feature at System → Tenants; re-login.
   - Verification: menu becomes accessible and endpoints return 200.

7) **Symptom:** “Run starts but never finishes”
   - Likely cause: worker down or job stuck.
   - Fix: check backend worker health and logs; cancel/retry.
   - Verification: status transitions to completed/failed with reason.

8) **Symptom:** Sandbox/prod confusion
   - Likely cause: running scenarios with production assumptions.
   - Fix: clearly separate environments; enforce sandbox constraints.
   - Verification: no production-facing side effects.

9) **Symptom:** Export fails
   - Likely cause: export endpoint not implemented.
   - Fix: use supported download mechanism.
   - Verification: export file generated.

---

## 7) Resolution steps (step-by-step)

1) Confirm user/tenant has `can_use_game_robot`.
2) Capture failing endpoint + status.
3) Check backend logs for job runner issues.
4) Reduce scenario complexity.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Overview shows runs.
- Status badges transition properly.

### 8.2 System → Logs
- Look for job failures and repeated errors.

### 8.3 App / container logs
- Search keywords:
  - `simulation`
  - `simulator`
  - `run`
  - `job` / `worker`

### 8.4 System → Audit Log
- Expected audit events (if implemented): `simulation.executed`.

### 8.5 Database audit (if present)
- Runs storage depends on deployment.
- Evidence should include run id, actor, inputs, and timestamps.

---

## 9) Security notes + rollback

- Simulation features should be sandboxed.
- If simulation impacts production behavior:
  - disable simulator feature
  - collect evidence
  - follow incident process

---

## 10) Related links

- Tenants (feature enable): `/docs/new/en/admin/system/tenants.md`
- Math Assets: `/docs/new/en/admin/game-engine/math-assets.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
