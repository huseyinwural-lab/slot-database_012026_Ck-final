# Onboarding Paketi (1. Gün)

## Ops Ekibine Hoş Geldiniz

### 1. Erişim Kurulumu
- **VPN:** `vpn.casino.com` (IDM üzerinden erişim talep edin)
- **Admin Paneli:** `https://admin.casino.com` (SSO Girişi)
- **İzleme:** Grafana / Kibana erişimi

### 2. Kritik Araçlar
- **Denetim Görüntüleyici:** İncelemeler için Admin Paneli’nde `/audit` kullanın.
- **Ops Durumu:** Sistem sağlığı için `/ops` kullanın.
- **Scriptler:** Bakım araçları için `app/scripts/` deposunu checkout edin.

### 3. "Kırmızı Çizgiler" (Aşmayın)
- **ASLA** `auditevent` tablosundan manuel silme yapmayın (purge script’ini kullanın).
- **ASLA** CTO onayı olmadan Prod ortamında `prevent_audit_delete` trigger’ını devre dışı bırakmayın.
- **ASLA** `AUDIT_EXPORT_SECRET` paylaşmayın.

### 4. İlk Görevler
1. `operating_handoff_bau.md` dosyasını okuyun.
2. Akışı anlamak için lokalinizde dry-run arşiv dışa aktarımı çalıştırın.
3. `#ops-alerts` kanalına katılın.