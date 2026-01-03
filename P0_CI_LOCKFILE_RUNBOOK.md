# P0 CI LOCKFILE RUNBOOK (FINAL)

## Problem
CI şu adımda FAIL ediyor:
yarn install --frozen-lockfile
makefile:
Hata:
Your lockfile needs to be updated
Yaml:

Sebep:
- `frontend/package.json` güncel
- `frontend/yarn.lock` güncel değil
- Bu iki dosya senkron olmadığı için CI deterministik olarak FAIL eder

Bu bir CI veya config problemi değildir.

---

## KAPSAM
Bu runbook **SADECE** aşağıdaki dosya içindir:
frontend/yarn.lock
markdown:

Aşağıdaki klasörler **KAPSAM DIŞIDIR**:
- `.emergent/`
- `frontend-player/`
- `e2e/`
- `backend/`

---

## TEK DOĞRU ÇÖZÜM

### 1) Doğru branch
```bash
git checkout main
git pull origin main
2) Lockfile üretimi (zorunlu)
Bash:
cd frontend
rm -rf node_modules
yarn cache clean
yarn install
3) Kontrol
Bash:
git status
Beklenen:
Bash:
modified: frontend/yarn.lock
Başka dosya OLMAMALI.
________________________________________
4) Commit + Push
Bash:
git add frontend/yarn.lock
git commit -m "chore(frontend): sync yarn.lock for frozen-lockfile CI"
git push origin main
5) GitHub UI doğrulama
•	frontend/yarn.lock
•	"Last commit" → dakikalar önce olmalı
•	“3 weeks ago” görünüyorsa işlem BAŞARISIZDIR
________________________________________
6) CI
•	frontend-lint.yml yeniden çalıştırılır
•	Beklenen sonuç:
frontend-lint PASS
________________________________________
YAPILMAYACAKLAR
•	yarn.lock manuel editlenmez
•	Başka dosya commit edilmez
•	Debug / test eklenmez
•	Alternatif çözüm denenmez
________________________________________
KAPANIŞ KRİTERİ
frontend-lint PASS
Bu sağlandığında P0 gate KAPANMIŞ kabul edilir.
Yaml:

---

## Nasıl kullanacaksın?
- Bu dosyayı repo köküne ekle
- Yazılımcıya **“sadece bu dosyayı uygula”** de
- Slack / mail / WhatsApp’ta açıklama yapma

İstersen bir sonraki adımda:
- 📌 **Bu dosyayı README’ye bağlayalım**
- 📌 veya **CI fail olduğunda otomatik link verelim**
