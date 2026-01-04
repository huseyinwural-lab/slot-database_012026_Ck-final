# Operations Manual (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Platform Engineering  

This manual is for real-world operations. It complements Quickstart.

---

## 1) Deploy models

### 1.1 Docker Compose

- Use compose for small environments or acceptance deployments.
- Keep secrets out of compose files.

Legacy references:
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `/docs/CI_PROD_COMPOSE_ACCEPTANCE.md`

### 1.2 Kubernetes

- Use a secret manager integration (ExternalSecrets/Vault).
- Use readiness/liveness probes.
- Enforce `/api` routing via ingress.

---

## 2) Secrets management

See:
- `/docs/new/en/guides/secrets.md`

---

## 3) Observability (minimum)

### 3.1 Logs

- Use structured log schema.
- Ensure redaction rules are followed.

See:
- `/docs/ops/log_schema.md`
- `/docs/new/en/architecture/audit-logging.md`

### 3.2 Metrics/tracing

If not implemented, minimum requirement:
- error rate (5xx)
- webhook failure rate
- payout status transition time

---

## 4) Backup / restore & data lifecycle

See:
- `/docs/new/en/architecture/data-lifecycle.md`
- `/docs/new/en/runbooks/ops.md`

---

## 5) Incident runbooks

See:
- `/docs/new/en/runbooks/incident.md`

---

## 6) Release checklist + rollback

See:
- `/docs/new/en/runbooks/release.md`

---

## 7) Multi-tenant lifecycle

See:
- `/docs/new/en/admin/tenant-lifecycle.md`
- `/docs/new/en/architecture/tenancy.md`

Key guarantees:
- platform owner creates tenants
- tenant admin cannot delete tenants
- system tenant is protected

---

## 8) Break-glass

See:
- `/docs/new/en/admin/password-reset.md`
- `/docs/new/en/architecture/audit-logging.md`

Policy:
- break-glass actions must be time-bounded and audited
