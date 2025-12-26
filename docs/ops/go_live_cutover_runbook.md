# Go-Live Cutover Runbook

**Version:** 1.0 (Final)
**Date:** 2025-12-26

## 1. Pre-Cutover Checks
- [ ] **Secrets:** Verify all prod secrets are injected (Use `d4_secrets_checklist.md`).
- [ ] **DB:** Confirm Alembic is at `head`.
- [ ] **Backup:** Take "Point-in-Time" snapshot immediately before traffic switch.

## 2. Migration
```bash
# Production
./scripts/start_prod.sh --migrate-only
```

## 3. Maintenance Mode (Optional)
If migrating from legacy:
1. Enable "Maintenance Mode" page on LB/Cloudflare.
2. Stop old traffic.

## 4. Health Verification
1. Check `/api/v1/ops/health` -> Must be GREEN.
2. Check Ops Dashboard `/ops`.
3. Verify Remote Storage connection (Archive upload test).

## 5. Traffic Cutover
1. Update DNS / LB rules to point to new cluster.
2. Tail logs for 5xx spikes.
3. Monitor `d4_ops_dashboard` for anomalies.

## 6. Post-Go-Live Smoke
1. **Finance:** Process 1 real low-value deposit and withdrawal (Ops Wallet).
2. **Game:** Launch 1 game, spin 10 times.
3. **Audit:** Verify actions appeared in Audit Log.

## 7. Hypercare (24h)
- On-Call rotation active.
- Slack channel `#ops-war-room` monitoring.
- Hourly check of Reconciliation Reports.
