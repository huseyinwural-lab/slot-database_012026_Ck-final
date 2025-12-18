# DR Checklist (03:00 Operator) (P4.1)

> Use this page during an incident. It is intentionally short and command-driven.

References:
- Runbook: `docs/ops/dr_runbook.md`
- RTO/RPO targets: `docs/ops/dr_rto_rpo.md`
- Proof template (canonical): `docs/ops/restore_drill_proof/template.md`
- Log schema contract: `docs/ops/log_schema.md`

---

## 1) Declare incident

1) Set severity and owner:
- Severity: SEV-1 / SEV-2 / SEV-3
- Incident commander (IC): <name>
- Comms owner: <name>

2) Record timestamps:
- `incident_start_utc`: `date -u +%Y-%m-%dT%H:%M:%SZ`

3) Create a proof file:
- Copy: `docs/ops/restore_drill_proof/template.md` → `docs/ops/restore_drill_proof/YYYY-MM-DD.md`
- Mark it as **INCIDENT PROOF** at top.

---

## 2) Containment

Pick what applies:

### A) Maintenance mode / traffic stop
- **K8s:** scale to zero (fastest containment)
  ```bash
  kubectl scale deploy/frontend-admin --replicas=0
  kubectl scale deploy/backend --replicas=0
  ```
- **Compose/VM:** stop the stack (or at least backend)
  ```bash
  docker compose -f docker-compose.prod.yml stop backend frontend-admin
  ```

### B) Admin login freeze (optional)
If you have a kill-switch/feature flag, enable it.
If not available, treat as N/A.

---

## 3) Identify scenario (choose one)

- [ ] **Scenario A (App-only):** UI/API broken, DB likely healthy.
- [ ] **Scenario B (DB issue):** corruption / wrong migration / schema mismatch / data loss.
- [ ] **Scenario C (Infra loss):** node/host down (VM host loss or K8s node/region).

Then jump to the matching runbook section in `docs/ops/dr_runbook.md`.

---

## 4) Execute (commands)

### Common quick signals
- Version:
  ```bash
  curl -fsS -i <URL>/api/version
  ```
- Health/ready:
  ```bash
  curl -fsS -i <URL>/api/health
  curl -fsS -i <URL>/api/ready
  ```

### Scenario A: App-only (rollback app image)
- **K8s:**
  ```bash
  kubectl rollout undo deploy/backend
  kubectl rollout status deploy/backend
  kubectl rollout undo deploy/frontend-admin
  kubectl rollout status deploy/frontend-admin
  ```
- **Compose/VM:**
  ```bash
  # pin previous image tags in docker-compose.prod.yml
  docker compose -f docker-compose.prod.yml up -d
  ```

### Scenario B: DB issue (contain → evaluate → restore)
- **Evaluate migrations (if Alembic is used):**
  ```bash
  docker compose -f docker-compose.prod.yml exec -T backend alembic current
  ```
- **Restore from backup (preferred baseline):**
  ```bash
  ./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
  docker compose -f docker-compose.prod.yml restart backend
  ```

### Scenario C: Infra loss
- **K8s:**
  ```bash
  kubectl get pods -A
  kubectl rollout status deploy/backend
  ```
- **VM host loss:**
  - Provision new host
  - Restore Postgres volume (or restore from backup)
  - Redeploy known-good images

---

## 5) Validate (must-pass)

### APIs
- `/api/health` → 200
- `/api/ready` → 200
- `/api/version` → expected

### Owner capabilities
- Acquire token (example):
  ```bash
  curl -s -X POST <URL>/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@casino.com","password":"***"}'
  ```
- Check capabilities:
  ```bash
  curl -s <URL>/api/v1/tenants/capabilities -H "Authorization: Bearer ***"
  ```

Expected:
- `is_owner=true`

### UI smoke (owner)
- Login
- Tenants list loads
- Settings → Versions loads
- Logout works

### Logs (contract-based)
Using your log system, confirm:
- 5xx rate is dropping (filter `event=request` AND `status_code>=500`)
- latency returns to baseline (p95 of `duration_ms`)
- correlate errors via `request_id`

---

## 6) Proof + Postmortem

1) Fill the proof file (commands + outputs), redact secrets.
2) Record RTO/RPO measurements (see `docs/ops/dr_rto_rpo.md`).
3) Schedule postmortem:
- root cause
- corrective actions
- follow-ups
