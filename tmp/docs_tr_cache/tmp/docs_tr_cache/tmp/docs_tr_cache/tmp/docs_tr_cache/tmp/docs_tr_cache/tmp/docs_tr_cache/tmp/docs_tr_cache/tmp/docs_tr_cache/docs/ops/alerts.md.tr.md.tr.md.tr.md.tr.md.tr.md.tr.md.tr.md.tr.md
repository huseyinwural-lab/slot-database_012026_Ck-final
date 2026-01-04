# İzleme ve Uyarı Temel Düzeyi (P3.3)

Amaç: staging/prod için **minimum, yüksek sinyal** veren bir uyarı seti tanımlamak.

> Bu doküman bilinçli olarak araçtan bağımsızdır (Prometheus/Grafana, Datadog, ELK, CloudWatch).

## 1) Kullanılabilirlik (birini sayfala)

### A1) Readiness başarısız
- Sinyal: `/api/ready` > 2 dakika boyunca 200 olmayan döner
- Önem derecesi: **kritik**
- Muhtemel nedenler:
  - DB’ye ulaşılamıyor
  - migration’lar eksik/bozuk

### A2) Artmış 5xx oranı
- Sinyal: 5xx oranı 5 dakika boyunca > %1 (veya 10 dakika boyunca > %0.5)
- Önem derecesi: **kritik**
- Notlar:
  - Gürültüyü azaltmak için endpoint’e göre dilimle
  - `X-Request-ID` ile korelasyon kur

## 2) Gecikme (bozulma)

### L1) p95 API gecikmesi sıçraması
- Sinyal: p95 gecikme 10 dakika boyunca > 800ms (baseline sonrası ayarla)
- Önem derecesi: **yüksek**
- Notlar:
  - Ingress/load-balancer veya API gateway seviyesinde takip et

## 3) Güvenlik / Kötüye kullanım

### S1) Login rate-limited sıçramaları
- Sinyal: `auth.login_rate_limited` denetim (audit) olayı sayısı baseline’ın üzerinde (örnek: > 20 / 5 dk)
- Önem derecesi: **yüksek**
- Neden:
  - Olası credential stuffing
  - Bir release sonrası false positive’ler (bozuk login)

### S2) Login başarısızlıkları sıçraması
- Sinyal: `auth.login_failed` denetim (audit) olayları, geriye dönük baseline’a kıyasla sıçrar
- Önem derecesi: **orta**

## 4) Admin-risk olayları

### R1) Admin devre dışı bırakıldı/etkinleştirildi olayları
- Sinyal: `admin.user_disabled` VEYA `admin.user_enabled` denetim (audit) olayı
- Önem derecesi: **yüksek** (security/ops’a bildir)
- Notlar:
  - Bunlar tipik olarak nadirdir ve yüksek sinyal verir.

### R2) Tenant feature flag’leri değişti
- Sinyal: `tenant.feature_flags_changed` denetim (audit) olayı
- Önem derecesi: **orta**

## 5) Önerilen dashboard’lar

- API genel bakış: RPS, 2xx/4xx/5xx, p95 gecikme
- Auth dashboard’u: login_success/login_failed/login_rate_limited
- Tenant kapsamlaması: `X-Tenant-ID` kullanımı, tenant_id kırılımı
- Audit trail: son 24 saat yüksek riskli olaylar

## 6) Runbook işaretçileri

Bir uyarı tetiklendiğinde:
1) Backend `GET /api/version` kontrol et (hangi build çalışıyor)
2) Loglarda `event=service.boot` ara ve `X-Request-ID` ile korelasyon kur
3) Rollback gerekiyorsa: `docs/ops/rollback.md` dosyasına bak
4) DB şema uyumsuzluğu şüpheleniliyorsa: `docs/ops/migrations.md` dosyasına bak
5) Veri bozulması şüpheleniliyorsa: yedekten geri yükle (`docs/ops/backup.md` dosyasına bak)

## 7) Log şeması sözleşmesi referansı

Bu uyarı temel düzeyi, aşağıda dokümante edilen backend JSON log sözleşmesini varsayar:
- `docs/ops/log_schema.md`

Bu uyarıların kullandığı ana alanlar:
- korelasyon: `request_id`
- HTTP health/5xx: `event=request`, `status_code`, `path`
- gecikme: `duration_ms`