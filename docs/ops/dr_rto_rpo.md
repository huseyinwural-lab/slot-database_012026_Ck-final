# DR RTO / RPO Targets (P4.1)

## Definitions

- **RTO (Recovery Time Objective):** maximum acceptable time from **incident start** to **service restored** (validated healthy).
- **RPO (Recovery Point Objective):** maximum acceptable **data loss window** measured as time between the latest restorable backup point and the incident time.

## Baseline targets (current reality)

These targets assume **daily backups** (see `docs/ops/backup.md`).

### Staging / Prod-compose
- **RTO:** 60–120 minutes
- **RPO:** 24 hours

### Kubernetes (if cluster + manifests + PVC/Secrets are ready)
- **RTO:** 30–60 minutes
- **RPO:** 24 hours

## Optional improvement target (if you add more frequent backups)

If hourly backups are introduced:
- **RPO:** 1 hour

## Measurement method (must record)

### RTO measurement
Record:
- `incident_start_utc`: when the incident is declared (see `docs/ops/dr_checklist.md`)
- `recovery_complete_utc`: when all validation checks pass:
  - `GET /api/health` → 200
  - `GET /api/ready` → 200
  - `GET /api/version` → expected
  - owner capabilities show `is_owner=true`
  - UI smoke passes

RTO = `recovery_complete_utc - incident_start_utc`

### RPO measurement
Record:
- `backup_timestamp_utc`: timestamp of the backup artifact used
- `incident_start_utc`

RPO = `incident_start_utc - backup_timestamp_utc`

## Proof standard

For any DR event (real incident or drill), record proof using the canonical template:
- `docs/ops/restore_drill_proof/template.md`

Redact secrets/tokens per `docs/ops/restore_drill.md`.
