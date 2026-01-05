# Release Readiness Checklist (EN)

**Document:** Release Readiness Checklist  
**Release Owner:** Platform Owner  
**Scope:** Admin, Backend, Frontend, Ops  
**Decision:** GO / NO-GO (single owner)

---

## 0) Pre-flight

**Goal:** Release kararını verecek kişinin yetki ve bağlamı net olsun.

- Release Owner atanmış (Platform Owner)
- Target environment net (preview / staging / prod)
- Release window onaylı

**GO criteria:** Owner + environment net  
**NO-GO:** Owner belirsiz / yanlış environment

---

## 1) Auth & Access

**Risk:** Admin erişimi yok / yetkisiz erişim

### Checks

- Admin login başarılı
- Session/token oluşuyor
- Role & scope doğru
- Break-glass hesabı çalışıyor
- Login/logout audit’e yazılıyor

### Evidence

- UI: `/admin/login` → dashboard
- Audit Log: `admin.login.success`

**GO:** Login + audit OK  
**NO-GO:** Login fail / audit yok

---

## 2) Tenant & Isolation

**Risk:** Yanlış tenant’a işlem / data sızıntısı

### Checks

- Tenant context açıkça görünüyor
- Tenant create → Platform Owner only
- System tenant silinemez
- Tenant-scoped işlemler `tenant_id` ile doğru

### Evidence

- UI: System → Tenants
- Audit: `tenant.create.attempt`, `tenant.created`

**GO:** Policy enforce ediliyor  
**NO-GO:** Tenant smuggling / yetkisiz create

---

## 3) Games & Catalog Operations

**Risk:** Oyunlar yanlış görünür / gelir kaybı

### Checks

- Games listesi yükleniyor
- Enable/disable çalışıyor
- VIP görünürlük kuralı doğru
- Provider connectivity OK
- Import gap’leri register’da takipte

### Evidence

- UI: Core → Games
- Logs: games, toggle, provider name

**GO:** Görünürlük doğru  
**NO-GO:** Yanlış segment / provider fail

---

## 4) Finance & Withdrawals

**Risk:** Para akışı bozulur

### Checks

- Deposit/withdraw temel akış OK
- Withdrawal approval queue çalışıyor
- Ledger tutarlılığı (basic sanity)
- Chargeback/dispute hook’ları (varsa) OK

### Evidence

- UI: Finance / Withdrawals
- Logs: ledger, withdrawal

**GO:** Para akışı sağlıklı  
**NO-GO:** Approval/ledger hatası

---

## 5) Risk & Compliance

**Risk:** Regülasyon ihlali

### Checks

- KYC verification çalışıyor
- Fraud rules evaluate ediliyor
- Responsible Gaming enforce ediliyor
- Manual override audit’leniyor

### Evidence

- UI: Operations → KYC / Risk
- Audit: `kyc.*`, `risk.*`

**GO:** Risk kontrolleri aktif  
**NO-GO:** KYC/Fraud bypass

---

## 6) Observability & Incident Readiness

**Risk:** Sorun olduğunda körlük

### Checks

- System → Logs erişilebilir
- Audit Log erişilebilir
- Kritik error’lar loglanıyor
- Incident runbook’lara erişim var

### Evidence

- UI: System → Logs / Audit Log

**GO:** Gözlemlenebilirlik var  
**NO-GO:** Log/Audit erişilemez

---

## 7) Data & Migrations

**Risk:** DB bozulur / servis açılmaz

### Checks

- Migration head uyumlu
- DB read/write OK
- Backup/restore notu mevcut

### Evidence

- Logs: alembic, migration

**GO:** DB sağlıklı  
**NO-GO:** Migration mismatch

---

## 8) CI / Release Gates

**Risk:** Kırık build prod’a gider

### Checks

- CI kritik job’lar yeşil
- `docs_smoke.sh` PASS
- Compose acceptance PASS

### Evidence

- GitHub Actions (yeşil)

**GO:** CI yeşil  
**NO-GO:** Kırmızı job

---

## 9) Rollback Plan (Minimum Viable)

**Risk:** Geri dönememe

### Checks

- Frontend rollback yolu net
- Backend rollback yolu net
- DB rollback policy net
- Kill Switch kriterleri biliniyor

### Evidence

- Runbooks: rollback / kill-switch

**GO:** Rollback mümkün  
**NO-GO:** Rollback belirsiz

---

## 🔒 Final Decision

Release Owner kararı:

- ☐ GO
- ☐ NO-GO

Notlar / Risk kabulü:

- …
