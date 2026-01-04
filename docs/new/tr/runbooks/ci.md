# CI Runbook (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Release Engineering  

Bu runbook, CI’da en sık görülen hata tiplerini ve deterministik çözüm yolunu içerir.

---

## 1) P0: `yarn install --frozen-lockfile` FAIL

Belirti:
- CI adımı şu hata ile fail: `Your lockfile needs to be updated`

Kök neden:
- `frontend/package.json` ile `frontend/yarn.lock` senkron değil.

Deterministik çözüm (repo kökünde):

```bash
git checkout main
git pull origin main

cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..

git status
# Beklenen: sadece frontend/yarn.lock modified

git add frontend/yarn.lock
git commit -m "chore(frontend): sync yarn.lock for frozen-lockfile CI"
git push origin main
```

Doğrulama:
- GitHub → `frontend/yarn.lock` → History: en üst commit **minutes ago** görünmeli.
- `frontend-lint.yml` rerun → **PASS**.

---

## 2) Compose acceptance / E2E

Legacy referans:
- `/docs/CI_PROD_COMPOSE_ACCEPTANCE.md`
- `/docs/E2E_SMOKE_MATRIX.md`

E2E network timeout gibi flakiness için payout polling gibi noktalarda deterministik retry/timeouts tercih edilmelidir.

---

## 3) Kapanış raporu (tek mesaj)

```text
frontend_lint PASS/FAIL
prod_compose_acceptance PASS/FAIL
release-smoke-money-loop PASS/FAIL
```
