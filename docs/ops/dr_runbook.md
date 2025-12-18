# Disaster Recovery Runbook (P4.1)

**Default recovery strategy:** restore-from-backup.

Guiding principles:
- **Data integrity > fastest recovery** (especially in prod).
- For DB mismatch / wrong migration: **contain → rollback app image**, then restore DB if integrity is in doubt.
- Proof standard: `docs/ops/restore_drill_proof/template.md`.
- Log validation uses the contract: `docs/ops/log_schema.md`.

Also see:
- Release decision tree: `docs/ops/release.md`
- Backup/restore: `docs/ops/backup.md`

---

## Global prerequisites (before you start)

1) Create incident proof file:
- Copy `docs/ops/restore_drill_proof/template.md` → `docs/ops/restore_drill_proof/YYYY-MM-DD.md`
- Mark as **INCIDENT PROOF**

2) Decide target platform (pick one):
- **Compose/VM** (docker compose)
- **Kubernetes** (kubectl)

3) Collect signals (run and paste into proof)

```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```

---

## Scenario A — App-only failure (DB OK)

### Detection
Symptoms:
- `/api/ready` fails OR elevated 5xx
- DB checks are clean (no corruption signals), or issues point to app release/regression.

Signals to capture (paste into proof):
- Health/ready:
  ```bash
  curl -i <URL>/api/health
  curl -i <URL>/api/ready
  ```
- Version:
  ```bash
  curl -i <URL>/api/version
  ```
- Logs:
  - filter `event=request` and aggregate `status_code>=500`
  - confirm DB is reachable (no connection errors)

### Containment
- **K8s (fast):**
  ```bash
  kubectl scale deploy/frontend-admin --replicas=0
  kubectl scale deploy/backend --replicas=0
  ```
- **Compose/VM:**
  ```bash
  docker compose -f docker-compose.prod.yml stop backend frontend-admin
  ```

### Recovery (rollback app image)

#### Kubernetes
```bash
kubectl rollout undo deploy/backend
kubectl rollout status deploy/backend
kubectl rollout undo deploy/frontend-admin
kubectl rollout status deploy/frontend-admin
```

#### Compose/VM
```bash
# pin previous image tags in docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

### Validation (must-pass)
```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```

Owner capabilities:
```bash
curl -s <URL>/api/v1/tenants/capabilities -H "Authorization: Bearer ***"
```

UI smoke:
- Login as owner
- Open Tenants list
- Settings → Versions
- Logout

Logs:
- Confirm 5xx rate dropping: filter `event=request` and aggregate `status_code>=500`

### Proof
- Paste command outputs in the incident proof file.
- Record RTO (see `docs/ops/dr_rto_rpo.md`).

---

## Scenario B — Wrong migration / DB mismatch

### Detection
Symptoms:
- Deploy followed by 5xx errors
- Logs indicate schema mismatch (e.g., missing columns/tables)
- Alembic version not at expected head (if Alembic is used)

### Containment
Stop traffic first.

- **K8s:**
  ```bash
  kubectl scale deploy/backend --replicas=0
  kubectl scale deploy/frontend-admin --replicas=0
  ```
- **Compose/VM:**
  ```bash
  docker compose -f docker-compose.prod.yml stop backend frontend-admin
  ```

### Recovery

#### Step 1: Roll back app image (reduce pressure)
- **K8s:**
  ```bash
  kubectl rollout undo deploy/backend
  kubectl rollout status deploy/backend
  ```
- **Compose/VM:**
  ```bash
  # pin previous backend image tag
  docker compose -f docker-compose.prod.yml up -d backend
  ```

#### Step 2: Evaluate DB migration state (if applicable)
- Compose example:
  ```bash
  docker compose -f docker-compose.prod.yml exec -T backend alembic current
  ```

Expected:
- output matches the last known-good migration head.

#### Step 3: Decision point — Hotfix-forward vs Restore

Choose **RESTORE FROM BACKUP** if any of the following are true:
- Data integrity is uncertain
- Schema mismatch persists after app rollback
- You suspect partial/failed migrations

Choose **HOTFIX-FORWARD** only if:
- You can ship a compatible migration/app fix quickly AND
- You are confident data integrity is preserved.

#### Step 4: Restore-from-backup (baseline)
```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
docker compose -f docker-compose.prod.yml restart backend
```

### Validation (must-pass)
```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```

DB sanity examples:
```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres -d casino_db -c 'select count(*) from tenant;'
```

Owner capabilities + UI smoke as in Scenario A.

Logs:
- Confirm 5xx rate is dropping and latency normalizing.

### Proof
- Include:
  - rollback commands executed
  - alembic current output (or N/A)
  - restore command output
  - validate outputs

---

## Scenario C — Host/Node loss (VM host loss or K8s node/region disruption)

### Detection
- Pods cannot be scheduled / node NotReady / persistent storage unavailable
- VM host down, volume missing, or networking failure

### Containment
- Ensure traffic is stopped (ingress/replicas=0) to prevent split-brain writes.

### Recovery

#### Kubernetes (node loss)
1) Check cluster state:
```bash
kubectl get nodes
kubectl get pods -A
```

2) Ensure stateful services (Postgres) have storage:
- If Postgres is managed: restore via provider snapshots/PITR.
- If Postgres is in-cluster: ensure PVC/PV is bound.

3) Reschedule app:
```bash
kubectl rollout status deploy/backend
kubectl rollout status deploy/frontend-admin
```

#### VM / Compose (host loss)
1) Provision new host.
2) Restore Postgres data:
- Prefer restoring the Postgres volume from snapshot, OR
- Restore from the latest logical backup using the P3 restore procedure.
3) Deploy known-good images:
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Validation (must-pass)
Same validation as Scenario A:
```bash
curl -i <URL>/api/health
curl -i <URL>/api/ready
curl -i <URL>/api/version
```

Owner capabilities + UI smoke.

### Proof
- Include the infra recovery steps taken and final validation outputs.

---

## Post-incident

1) Record RTO/RPO (see `docs/ops/dr_rto_rpo.md`).
2) Capture key logs by contract fields (`request_id`, `path`, `status_code`, `duration_ms`).
3) Create postmortem doc (root cause + actions + owners + deadlines).
