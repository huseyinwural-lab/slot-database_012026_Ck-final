# Monitoring & Alerting Baseline (P3.3)

Goal: define a **minimal, high-signal** alert set for staging/prod.

> This doc is intentionally tool-agnostic (Prometheus/Grafana, Datadog, ELK, CloudWatch).

## 1) Availability (page someone)

### A1) Readiness failing
- Signal: `/api/ready` returns non-200 for > 2 minutes
- Severity: **critical**
- Likely causes:
  - DB unreachable
  - migrations missing/broken

### A2) Elevated 5xx rate
- Signal: 5xx rate > 1% over 5 minutes (or > 0.5% for 10 minutes)
- Severity: **critical**
- Notes:
  - Slice by endpoint to avoid noise
  - Correlate via `X-Request-ID`

## 2) Latency (degradation)

### L1) p95 API latency spike
- Signal: p95 latency > 800ms for 10 minutes (tune after baseline)
- Severity: **high**
- Notes:
  - Track at the ingress/load-balancer or API gateway level

## 3) Security / Abuse

### S1) Login rate-limited spikes
- Signal: count of `auth.login_rate_limited` audit events > baseline (example: > 20 / 5 min)
- Severity: **high**
- Why:
  - Possible credential stuffing
  - False positives after a release (broken login)

### S2) Login failures spike
- Signal: `auth.login_failed` audit events spike vs trailing baseline
- Severity: **medium**

## 4) Admin-risk events

### R1) Admin disabled/enabled events
- Signal: `admin.user_disabled` OR `admin.user_enabled` audit event
- Severity: **high** (notify security/ops)
- Notes:
  - These are typically rare and high-signal.

### R2) Tenant feature flags changed
- Signal: `tenant.feature_flags_changed` audit event
- Severity: **medium**

## 5) Recommended dashboards

- API overview: RPS, 2xx/4xx/5xx, p95 latency
- Auth dashboard: login_success/login_failed/login_rate_limited
- Tenant scoping: `X-Tenant-ID` usage, tenant_id breakdown
- Audit trail: last 24h high-risk events

## 6) Runbook pointers

When an alert fires:
1) Check backend `GET /api/version` (what build is running)
2) Check logs for `event=service.boot` and correlate with `X-Request-ID`
3) If rollback needed: see `docs/ops/rollback.md`
4) If DB schema mismatch suspected: see `docs/ops/migrations.md`
5) If data corruption suspected: restore from backup (see `docs/ops/backup.md`)
