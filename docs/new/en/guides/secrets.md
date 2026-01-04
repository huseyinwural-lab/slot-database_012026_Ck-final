# Configuration & Secrets Management (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Platform Engineering / Security  

This guide defines how configuration and secrets should be handled across environments.

---

## 1) Principles

1) **No secrets in git**
2) **No secrets in logs**
3) **Separate per environment** (dev/staging/prod)
4) **Rotate safely** (document blast radius + rollback)

---

## 2) Configuration vs secrets

- **Configuration**: non-sensitive environment settings (feature flags, limits, URLs)
- **Secrets**: credentials and signing keys

Examples of secrets:
- database password
- JWT secret / signing keys
- webhook signing secrets
- payment provider API keys

---

## 3) Where secrets should live

Choose one source of truth per environment:

- **Kubernetes**: Secrets / ExternalSecrets (recommended)
- **CI/CD**: GitHub Actions Secrets (for build/deploy only)
- **Vault**: centralized secret store

Rule:
- `.env` files are for **local development only**.

---

## 4) Rotation playbook (minimal)

### 4.1 JWT secret rotation

Steps:
1) Add new key (dual-read, single-write if supported)
2) Deploy
3) Wait for TTL / session expiry
4) Remove old key

If dual-key is not supported:
- rotate during maintenance window
- force re-login

### 4.2 Webhook secret rotation

Steps:
1) Configure new secret in provider dashboard
2) Update backend secret
3) Deploy
4) Validate with test webhook delivery

---

## 5) CI/CD handling

- CI must never print secrets.
- Use masked secret variables.
- Prefer short-lived credentials.

---

## 6) Runtime mutable config

Prefer configuration that is:
- set via environment variables
- or stored per-tenant in DB (feature flags)

Legacy references:
- `/docs/ops/log_schema.md` (redaction rules)
- `/docs/payments/*` (provider secrets)
