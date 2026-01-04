# Canlıya Geçiş Cutover Runbook

**Versiyon:** 1.0 (Final)
**Tarih:** 2025-12-26

## 1. Cutover Öncesi Kontroller
- [ ] **Gizli Bilgiler:** Tüm prod gizli bilgilerinin enjekte edildiğini doğrulayın (`d4_secrets_checklist.md` kullanın).
- [ ] **DB:** Alembic’in `head` konumunda olduğunu doğrulayın.
- [ ] **Yedekleme:** Trafik geçişinden hemen önce "Point-in-Time" snapshot alın.

## 2. Migrasyon```bash
# Production
./scripts/start_prod.sh --migrate-only
```## 3. Bakım Modu (Opsiyonel)
Legacy’den migrasyon yapılıyorsa:
1. LB/Cloudflare üzerinde "Maintenance Mode" sayfasını etkinleştirin.
2. Eski trafiği durdurun.

## 4. Sağlık Doğrulaması
1. `/api/v1/ops/health` kontrol edin -> GREEN olmalı.
2. Ops Dashboard `/ops` kontrol edin.
3. Remote Storage bağlantısını doğrulayın (Archive upload testi).

## 5. Trafik Cutover
1. Yeni cluster’a işaret edecek şekilde DNS / LB kurallarını güncelleyin.
2. 5xx sıçramaları için logları tail edin.
3. Anomaliler için `d4_ops_dashboard` izleyin.

## 6. Canlıya Geçiş Sonrası Smoke Test
1. **Finans:** 1 adet gerçek düşük tutarlı yatırma ve çekme işlemi gerçekleştirin (Ops Wallet).
2. **Oyun:** 1 oyun başlatın, 10 kez çevirin.
3. **Denetim:** Aksiyonların Audit Log’da göründüğünü doğrulayın.

## 7. Hypercare (24s)
- On-Call rotasyonu aktif.
- Slack kanalı `#ops-war-room` takibi.
- Reconciliation Reports’un saatlik kontrolü.