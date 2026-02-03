# Casino Admin Platform – PRD

## Original Problem Statement
Full-stack casino admin platformında P0 stabilite ve prod readiness hedefleri. Öncelik: affiliate engine, Phase C UI sweep, kill switch doğrulama, güvenlik/RBAC ve son olarak prod readiness checklist (healthz/readyz + runbook).

## Kullanıcı Personaları
- **Platform Owner**: Tüm tenantları ve güvenlik/finans/operasyon metriklerini yönetir.
- **Tenant Admin / Ops**: Oyuncu, oyun, finans (withdrawal onayları) ve bonus yönetimi.
- **Support**: Görüntüleme ve destek süreçleri.

## Core Requirements (Özet)
- RBAC enforcement + audit logging
- Affiliate P0 engine
- Kill switch enforcement
- UI stabilizasyonu (tablo loading/error/empty standardizasyonu)
- Prod readiness: healthz/readyz + runbook + smoke test

## Mimari
- **Frontend**: React (craco), Tailwind UI
- **Backend**: FastAPI + SQLModel
- **DB**: Postgres (DATABASE_URL/POSTGRES_URL)
- **Cache/Queue**: Redis (opsiyonel)

## Uygulananlar (2026-02-03)
- `/api/v1/healthz` ve `/api/v1/readyz` endpoint’leri (DB + optional Redis)
- `docs/RUNBOOK.md` (migrasyon, bootstrap owner, log kontrolü)
- Golden Path smoke test: `e2e/tests/smoke-launch.spec.ts`
- Login/Logout data-testid eklendi
- Ops Header Health Widget (30sn polling, DB/Redis tooltip)
- Robots backend stub: `/api/v1/robots/status` → `{ status: "idle", active_bots: 0 }`
- Robots list stub: `/api/v1/robots` → `items: []`
- Finance approve/retry aksiyonları + Deposits tabı empty-state moduna alındı
- Settings placeholder sekmeleri + Currencies “Yakında” moduna alındı
- Deploy checklist env doğrulaması: `POSTGRES_URL` eklendi
- Sidebar’dan Advanced Analytics / Audit Logs / System Health kaldırıldı
- API Keys sayfası stabilize edildi (useTableState) + yetki kısıtlaması toastu
- Finance Deposits + aksiyonlar “Aktif işlem bulunmamaktadır” empty state’e çekildi
- Robots sayfası empty state + hata toast’ları sessize alındı (silent API)
- API client’ta `silent` flag ile global error toast baskılama eklendi
- Root `.env.example` merge edildi ve `REGISTER_VELOCITY_LIMIT=100` eklendi
- Frontend `yarn.lock` yeniden üretildi
- Velocity limit kontrolü: os.getenv + int() cast + 429 (Too many registration requests) koruması
- Docs smoke: root/backend/frontend/frontend-player `.env.example` dosyaları tamamlandı
- Frontend lint: `@eslint/js` 8.57.1 hizalandı + yarn.lock güncellendi
- Player register: tenant auto-create + IntegrityError yakalama (400) eklendi

## Test Durumu
- Backend: `/api/v1/healthz`, `/api/v1/readyz` curl PASS
- E2E: `smoke-launch.spec.ts` PASS

## Mocked API'ler
- `/api/v1/kyc/documents/{doc_id}/download` (mock download)
- Finance Deposits tab (HTTP 501 placeholder)

## Prioritized Backlog
### P0
- CI/CD pipeline failure logs (kullanıcı log paylaşımı bekleniyor)

### P1
- BONUS-P1: Wager/Turnover Engine
- BONUS-P1: Bonus State Machine & Expiry

### P2 (Frozen)
- KYC document storage (S3/GCS)
- CRM campaign infra
- Affiliate payouts lifecycle
- Chargeback evidence upload
- Reconciliation file upload
- Settings placeholder tabs backend
- Session refresh mechanism

## Next Action Items
1. Kullanıcıdan CI/CD loglarını al ve pipeline sorununu çöz.
2. Bonus wagering + expiry P1’lerine başla.
