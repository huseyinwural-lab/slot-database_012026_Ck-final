# P0 SHA / REMOTE CHECK (Neden “3 weeks ago” Görünüyor?)

Bu kontrol, “ben yaptım ama GitHub’da güncellenmiyor” problemini 1 dakikada ayırır.

## 1) Yanlış remote mu?
```bash
git remote -v
```

Beklenen: push URL **doğru repo** olmalı.

## 2) Yanlış branch mi?
```bash
git branch --show-current
git status
```

Beklenen: `main`

## 3) Push gerçekten gitmiş mi?
```bash
git log -1 --name-only
```

Beklenen:
- commit içinde `frontend/yarn.lock` görünmeli.

## 4) Push sonrası GitHub doğrulama
GitHub UI → `frontend/yarn.lock`:
- last commit “minutes ago” olmalı.

Hâlâ “3 weeks ago” ise %99:
- yanlış remote’a push
- yanlış branch’e push
- push yetkisi yok / push reject

---

## Yazılımcıya verilecek görev listesi (tek cümle)
“Repo kökünde `P0_CI_LOCKFILE_RUNBOOK.md` içindeki adımları uygula; sadece `frontend/yarn.lock` commit/push olacak; sonra `frontend-lint.yml` PASS ekran görüntüsü gönder.”
