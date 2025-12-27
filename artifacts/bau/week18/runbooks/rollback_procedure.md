# Rollback Procedure

## When to Rollback?
- Deployment failed health checks.
- Critical bug found immediately after deploy.
- Migration failure affecting data integrity.

## Steps

### 1. Database Rollback (If Migration involved)
- Check current head: `alembic current`
- Downgrade to previous revision: `alembic downgrade -1`
- **Warning:** Data loss possible if columns dropped. Verify data backup first.

### 2. Application Rollback
- Revert Git branch to previous tag: `git checkout <previous_tag>`
- Or use Container Image: `docker pull image:previous_tag`

### 3. Restart Services
- `supervisorctl restart backend`
- `supervisorctl restart frontend`

### 4. Verify
- Check `/api/health`
- Run Smoke Tests: `python3 /app/scripts/release_smoke.py`
