# Yazılımcı Görevi (FINAL) — P0 frozen-lockfile kapanış

## Amaç
- `frontend-lint.yml` içinde `yarn install --frozen-lockfile` FAIL kapanacak.

---

## Adımlar

### 1) Repo’yu güncelle
```bash
git checkout main
git pull origin main
```

### 2) Lockfile üret (mutlaka `frontend/` içinde)
```bash
cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..
```

### 3) Sadece `frontend/yarn.lock` değiştiğini doğrula
```bash
git status
```

### 4) Sadece bu dosyayı commit + push
```bash
git add frontend/yarn.lock
git commit -m "chore(frontend): sync yarn.lock for frozen-lockfile CI"
git push origin main
```

---

## Kanıt
- GitHub → `frontend/yarn.lock` → **History**’de en üst commit **dakikalar önce** olmalı
- GitHub Actions → `frontend-lint.yml` → **rerun** → **PASS**

---

## Tek mesaj rapor
```text
frontend_lint PASS/FAIL
prod_compose_acceptance PASS/FAIL
release-smoke-money-loop PASS/FAIL
```

---

## Not
Bu adım yapıldıktan sonra hâlâ FAIL varsa, ikinci aşama: CI’ın kullandığı SHA ile `main` SHA’sı uyuşuyor mu kontrolü; ama önce bu adımın gerçekleşmesi şart.
