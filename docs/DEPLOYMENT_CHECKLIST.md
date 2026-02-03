# Emergent Deployment Checklist

Bu repo Emergent’in **managed deployment** altyapısını kullanır.
Docker/Nginx config gerekmiyor.

## Deploy öncesi (UI/Prod readiness)
- [ ] `/app/test_result.md` güncel mi? Son Playwright suite PASS mi?
- [ ] P0 Money Loop Gate kapalı mı? (Deposit -> Withdrawal -> Settlement)
- [ ] RBAC enforcement PASS mi? (SEC-P0-02)
- [ ] Kill Switch enforcement PASS mi?
- [ ] “Coming Soon” placeholder’lar doğru mu? (feature yoksa fake data yok)

## Env doğrulama (Emergent UI -> Settings/Env)
- [ ] `DATABASE_URL` doğru mu?
- [ ] `JWT_SECRET` set mi?
- [ ] `CORS_ORIGINS` prod domain’i içeriyor mu?
- [ ] `REDIS_URL` gerekiyorsa set mi?
- [ ] Resend kullanılıyorsa: `RESEND_API_KEY`, `RESEND_FROM`, `RESEND_TEST_TO`

## Deploy adımı (Emergent)
- [ ] Preview çalışıyor mu?
- [ ] Deploy -> **Deploy Now**
- [ ] Deploy sonrası smoke:
  - [ ] Admin login
  - [ ] /players list
  - [ ] /games upload-import
  - [ ] /finance transactions + withdrawals

## Rollback
- [ ] Sorun olursa Emergent UI’dan **Rollback** (önceki checkpoint) kullan.
