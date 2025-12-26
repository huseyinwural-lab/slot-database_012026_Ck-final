# Operational Knowledge Base Index
**Single Source of Truth** for Platform Operations.

## 1. Core Documentation
| Document | Purpose | Location |
|---|---|---|
| **Master Runbook** | Day-to-day operations, war room protocol, rollback matrix. | [`/app/docs/ops/go_live_runbook.md`](./go_live_runbook.md) |
| **BAU Governance** | Reporting standards, rhythm, and action tracking rules. | [`/app/docs/ops/bau_governance.md`](./bau_governance.md) |
| **Executive Closeout** | Project history, evidence index, and initial risk register. | [`/app/docs/roadmap/executive_closeout_pack.md`](../roadmap/executive_closeout_pack.md) |
| **90-Day Roadmap** | Future reliability, security, and product plans. | [`/app/docs/roadmap/post_go_live_90_days.md`](../roadmap/post_go_live_90_days.md) |

## 2. Operational Toolchain (Scripts)
All scripts are located in `/app/scripts/`.

| Script | Usage | Frequency |
|---|---|---|
| `verify_prod_env.py` | Validates env vars, secrets, CORS. | Pre-flight / Change |
| `go_live_smoke.sh` | Checks migrations, health, login, router. | After Deploy |
| `detect_stuck_finance_jobs.py` | Finds payouts/txs stuck in intermediate states. | Cron (30m) |
| `daily_reconciliation_report.py` | Generates volume and risk summary. | Daily |
| `db_restore_drill.sh` | Backup/Restore verification (Staging only for restore). | Backup (Prod) / Drill (Stg) |

## 3. Critical Endpoints
*   **Health:** `GET /api/health`
*   **Admin Login:** `POST /api/v1/auth/login`
*   **Payouts Router:** `OPTIONS /api/v1/payouts/initiate`
*   **Ops Dashboard:** `GET /api/v1/ops/dashboard`

## 4. Evidence & Artifact Archives
*   **RC Proofs:** `/app/artifacts/rc-proof/` (Hashed)
*   **Go-Live Logs:** `/app/artifacts/sprint_7_execution_log.md`
*   **Canary Report:** `/app/artifacts/canary_report_filled.md`
*   **Waiver Register:** `/app/artifacts/prod_env_waiver_register.md`
*   **BAU Reports:** `/app/artifacts/bau/` (Standard location)

## 5. Escalation & Severity
*   **Sev-1 (Immediate):** 5xx Spike, Payout Failure > 5%, Ledger Invariant Breach. -> **Call Incident Commander.**
*   **Sev-2 (Urgent):** Queue Backlog > SLA, Webhook Failures > 1%. -> **Ticket + Slack Alert.**
*   **Sev-3 (Warning):** Single stuck job, Latency drift. -> **Next Business Day.**
