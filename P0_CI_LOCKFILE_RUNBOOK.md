# P0 CI LOCKFILE RUNBOOK (FINAL)

## Hata
CI şu adımda FAIL:
- `yarn install --frozen-lockfile`

Hata mesajı:
- `Your lockfile needs to be updated`

## Kök Sebep (Net)
`frontend/package.json` ile `frontend/yarn.lock` senkron değil.
Bu bir CI/config sorunu değil; lockfile güncelleme sorunu.

## Kapsam
Sadece şu dosya düzeltilecek ve commit edilecek:
- `frontend/yarn.lock`

## Uygulama (Tek Hamle)
> Repo kökünde çalıştır.

### 1) Doğru branch ve güncel kod
```bash
git checkout main
git pull origin main
```

### 2) Lockfile üret (mutlaka frontend içinde)
```bash
cd frontend
rm -rf node_modules
yarn cache clean
yarn install
cd ..
```

### 3) Sadece yarn.lock değiştiğini doğrula
```bash
git status
```

Beklenen:
- `modified: frontend/yarn.lock`

Başka dosya varsa: **staged etme / commit etme**.

### 4) Commit + push (sadece yarn.lock)
```bash
git add frontend/yarn.lock
git commit -m "chore(frontend): sync yarn.lock for frozen-lockfile CI"
git push origin main
```

## Doğrulama
GitHub → `frontend/yarn.lock`:
- "Last commit" **dakikalar önce** görünmeli.

## Başarı Kriteri
GitHub Actions:
- `frontend-lint.yml` **PASS**