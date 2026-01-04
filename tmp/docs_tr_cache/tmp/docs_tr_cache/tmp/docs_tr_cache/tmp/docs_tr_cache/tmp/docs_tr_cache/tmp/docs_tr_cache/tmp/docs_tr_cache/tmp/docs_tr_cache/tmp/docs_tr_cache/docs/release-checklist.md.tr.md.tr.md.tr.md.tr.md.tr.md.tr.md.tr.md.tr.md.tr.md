# Yayın Kontrol Listesi (Staging / Production)

## 1) CI / Kalite geçitleri
- [ ] GitHub Actions: **Prod Compose Acceptance** iş akışı YEŞİL
- [ ] Playwright E2E testleri BAŞARILI

## 2) Ortam / Secrets
- [ ] `ENV=staging` veya `ENV=prod` doğru ayarlanmış
- [ ] `JWT_SECRET` güçlü (varsayılan değil)
- [ ] `POSTGRES_PASSWORD` güçlü
- [ ] `DATABASE_URL` doğru ve hedeflenen Postgres’e işaret ediyor
- [ ] `CORS_ORIGINS` bir allowlist (prod/staging’de `*` yok)
- [ ] `TRUSTED_PROXY_IPS`, `X-Forwarded-For`’a güvenmek istiyorsanız harici reverse proxy IP(ler)inize ayarlanmış
- [ ] `LOG_FORMAT=auto` (veya `json`) ve loglar stack’iniz tarafından okunabilir (Kibana/Grafana)
- [ ] Denetim (audit) saklama süresi yapılandırılmış (90 gün) + temizleme prosedürü mevcut (`docs/ops/audit_retention.md`)

## 3) Bootstrap kuralı
- [ ] Kararlı durum production’da `BOOTSTRAP_ENABLED=false`
- [ ] Bootstrap gerekiyorsa geçici olarak etkinleştirin, owner oluşturun, sonra devre dışı bırakın ve yeniden deploy edin

## 4) Deploy
- [ ] `docker compose -f docker-compose.prod.yml build`
- [ ] `docker compose -f docker-compose.prod.yml up -d`
- [ ] Harici reverse proxy yönlendirmeleri:
  - `admin.domain.tld` -> admin UI container
  - `player.domain.tld` -> player UI container
  - `/api/*` UI container’a (same-origin) yönlendirilmeli, doğrudan backend’e değil

## 5) Deploy sonrası smoke testleri
Çalıştırın:
- [ ] `docker compose -f docker-compose.prod.yml ps`
- [ ] `curl -fsS http://127.0.0.1:8001/api/health`
- [ ] `curl -fsS http://127.0.0.1:8001/api/ready`
- [ ] Tarayıcı kontrolü: `https://admin.domain.tld` giriş çalışıyor ve Network `https://admin.domain.tld/api/v1/...` gösteriyor

## 6) Yedekleme hazırlığı
- [ ] Yedekleme script’i test edildi: `./scripts/backup_postgres.sh`
- [ ] Geri yükleme adımları anlaşıldı: `docs/ops/backup.md`

## 7) Sürümleme / rollback önerisi
- [ ] Image/release’leri etiketleyin (veya son bilinen-iyi artefact’leri saklayın)
- [ ] Rollback için önceki compose + env’i saklayın

## 8) Release tag + build metadata (P3)
- [ ] Release tag `vX.Y.Z-<gitsha>` kullanır (staging/prod’da `latest` yok)
- [ ] Backend boot log’u `version/git_sha/build_time` ile `event=service.boot` içerir
- [ ] Backend sürüm endpoint’i: `GET /api/version` beklenen `service, version, git_sha, build_time` döndürür
- [ ] Admin UI Settings → Versions sekmesi UI sürümü + git sha + build time gösterir

## 9) Kritik smoke (uygulama)
- [ ] Başarılı giriş `auth.login_success` audit event’ini yazar
- [ ] Tenants listesi + oluşturma çalışır (owner)
- [ ] Audit listesi çalışır: `GET /api/v1/audit/events?since_hours=1&limit=10`