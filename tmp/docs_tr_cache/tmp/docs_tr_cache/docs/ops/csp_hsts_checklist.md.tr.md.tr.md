# CSP + HSTS Kontrol Listesi (03:00 Operatörü) (P4.3)

Kanonik referanslar:
- Politika: `docs/ops/csp_policy.md`
- Yayınlama planı: `docs/ops/security_headers_rollout.md`
- Nginx parçacıkları:
  - `docs/ops/snippets/security_headers.conf`
  - `docs/ops/snippets/security_headers_report_only.conf`
  - `docs/ops/snippets/security_headers_enforce.conf`

---

## STG-SecHeaders-01 (staging etkinleştirme)

Kubernetes UI-nginx bağlantılama varsayımı:
- ConfigMap, frontend-admin nginx içine bağlanır:
  - `k8s/frontend-admin-security-headers-configmap.yaml`
- Geri alma kolu (tek anahtar):
  - `SECURITY_HEADERS_MODE=off|report-only|enforce`

Değişiklik:
- Ayarla: `SECURITY_HEADERS_MODE=report-only`

Doğrula (başlıklar):```bash
export STAGING_DOMAIN="<fill-me>"
curl -I "https://${STAGING_DOMAIN}/" | egrep -i "content-security-policy|strict-transport-security"
```Beklenen:
- `Content-Security-Policy-Report-Only` mevcut
- `Strict-Transport-Security` mevcut (düşük max-age)

Doğrula (UI):
- Giriş
- Kiracılar
- Ayarlar
- Çıkış

İhlalleri topla:
- **≥ 7 gün** boyunca report-only olarak tut
- Engellenen URL'leri + direktifleri yakala (konsol veya rapor uç noktası)

Geri alma (< 5 dk):
- Ayarla: `SECURITY_HEADERS_MODE=off` ve frontend-admin pod’unu yeniden dağıt/yeniden başlat.

---

## 2) Allowlist’i güncelle

Değişiklik:
- Politikaya yalnızca gözlemlenen/onaylanan kaynakları ekle (bkz. `docs/ops/csp_policy.md`).

Doğrula:
- UI smoke + ihlallerin azaldığını doğrula.

---

## 3) CSP Enforce’a geçiş

Geçiş koşulu:
- ≥ 7 gün ihlal verisi
- allowlist güncellendi

Değişiklik:
- Ayarla: `SECURITY_HEADERS_MODE=enforce`

Doğrula:```bash
export STAGING_DOMAIN="<fill-me>"
curl -I "https://${STAGING_DOMAIN}/" | grep -i content-security-policy
```Beklenen:
- `Content-Security-Policy` mevcut

UI smoke + hata oranlarını izle.

Geri alma (< 5 dk):
- Ayarla: `SECURITY_HEADERS_MODE=report-only` ve frontend-admin pod’unu yeniden dağıt/yeniden başlat.

---

## 4) Sıkılaştır

Değişiklik:
- Geçici izinleri (süreye bağlı) kaldır, özellikle scriptler için herhangi bir `unsafe-inline`.

Doğrula:
- UI smoke + yeni ihlal yok.

Geri alma (< 5 dk):
- Önceki bilinen-iyi include/politikaya geri dön.

---

## 5) HSTS staging

Varsayılan (bu görev):
- HSTS, `SECURITY_HEADERS_MODE=report-only` içinde zaten etkin ve şu şekilde:
  - `max-age=300`
  - includeSubDomains yok
  - preload yok

Doğrula:```bash
export STAGING_DOMAIN="<fill-me>"
curl -I "https://${STAGING_DOMAIN}/" | grep -i strict-transport-security
```Geri alma (< 5 dk):
- Ayarla: `SECURITY_HEADERS_MODE=off` ve frontend-admin pod’unu yeniden dağıt/yeniden başlat.

---

## 6) HSTS prod kademeli artırma

Değişiklik:
- Gün 1: `max-age=300`
- Gün 2: `max-age=3600`
- Gün 3: `max-age=86400`
- 2. hafta+: `max-age=31536000`

Varsayılan duruş:
- `includeSubDomains`: HAYIR
- `preload`: HAYIR

Doğrula:```bash
curl -I https://<prod-admin-domain>/ | grep -i strict-transport-security
```Geri alma (< 5 dk):
- Ayarla: `SECURITY_HEADERS_MODE=off` ve frontend-admin pod’unu yeniden dağıt/yeniden başlat.