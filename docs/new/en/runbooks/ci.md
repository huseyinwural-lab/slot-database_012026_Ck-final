# CI Runbook (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Release Engineering  

This runbook covers the most common CI failure modes and the deterministic fix path.

---

## 1) P0: `yarn install --frozen-lockfile` fails

Symptom:
- CI step fails with: `Your lockfile needs to be updated`

Cause:
- `frontend/package.json` and `frontend/yarn.lock` are not synchronized.

Deterministic fix (repo root):

```bash
git checkout main
git pull origin main

cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..

git status
# Expect: only frontend/yarn.lock modified

git add frontend/yarn.lock
git commit -m "chore(frontend): sync yarn.lock for frozen-lockfile CI"
git push origin main
```

Verification:
- GitHub → `frontend/yarn.lock` → History: latest commit should be **minutes ago**.
- Re-run `frontend-lint.yml` → **PASS**.

---

## 2) Compose acceptance / E2E

Key workflows (legacy details):
- `/docs/CI_PROD_COMPOSE_ACCEPTANCE.md`
- `/docs/E2E_SMOKE_MATRIX.md`

If E2E is flaky due to network timeouts, prefer deterministic waits/retries around payout polling.

---

## 3) Closing report (single message)
After CI finishes, report:

```text
frontend_lint PASS/FAIL
prod_compose_acceptance PASS/FAIL
release-smoke-money-loop PASS/FAIL
```
