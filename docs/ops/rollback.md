# Rollback Runbook (P3-REL-004)

## Goal
Rollback the application to a **previous known-good image tag** within ~15 minutes.

## Assumptions
- Deployments are pinned to tags: `vX.Y.Z-<gitsha>` (no `latest`).
- DB migration strategy is documented separately (see `docs/ops/migrations.md`).

## Compose rollback (example)
1) Identify previous tag (example): `v1.3.9-7ac0f2b`
2) Update compose to use the previous tag:

```yaml
services:
  backend:
    image: registry.example.com/casino/backend:v1.3.9-7ac0f2b
  frontend-admin:
    image: registry.example.com/casino/frontend-admin:v1.3.9-7ac0f2b
  frontend-player:
    image: registry.example.com/casino/frontend-player:v1.3.9-7ac0f2b
```

3) Re-deploy:

```bash
docker compose -f docker-compose.prod.yml up -d
```

4) Verify:
- `curl -fsS http://127.0.0.1:8001/api/ready`
- `curl -fsS http://127.0.0.1:8001/api/version`
- Check boot logs for `event=service.boot`

## Kubernetes rollback (short example)
Option A: Rollout undo

```bash
kubectl rollout undo deploy/backend
```

Option B: Pin previous image tag

```bash
kubectl set image deploy/backend backend=registry.example.com/casino/backend:v1.3.9-7ac0f2b
kubectl rollout status deploy/backend
```

## Config/env compatibility notes
- If the new release introduced **required** env vars, ensure the old release still has them (or remove/revert them).
- If migrations are forward-only, DB rollback may require restore from backup.
