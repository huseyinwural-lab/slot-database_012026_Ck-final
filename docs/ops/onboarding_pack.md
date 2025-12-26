# Onboarding Pack (Day 1)

## Welcome to Ops Team

### 1. Access Setup
- **VPN:** `vpn.casino.com` (Request access via IDM)
- **Admin Panel:** `https://admin.casino.com` (SSO Login)
- **Monitoring:** Grafana / Kibana access

### 2. Critical Tools
- **Audit Viewer:** Use `/audit` in Admin Panel for investigations.
- **Ops Status:** Use `/ops` for system health.
- **Scripts:** Checkout repo `app/scripts/` for maintenance tools.

### 3. "Red Lines" (Do Not Cross)
- **NEVER** manually delete from `auditevent` table (use purge script).
- **NEVER** disable `prevent_audit_delete` trigger in Prod without CTO approval.
- **NEVER** share `AUDIT_EXPORT_SECRET`.

### 4. First Tasks
1. Read `operating_handoff_bau.md`.
2. Run a dry-run archive export locally to understand the flow.
3. Join `#ops-alerts` channel.
