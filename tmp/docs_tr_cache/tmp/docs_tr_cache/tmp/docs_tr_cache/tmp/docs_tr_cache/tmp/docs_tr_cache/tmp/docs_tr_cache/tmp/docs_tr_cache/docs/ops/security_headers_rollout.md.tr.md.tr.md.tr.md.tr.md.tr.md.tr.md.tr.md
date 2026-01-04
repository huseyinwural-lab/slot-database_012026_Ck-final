# CSP + HSTS Yaygınlaştırma Planı (P4.3)

Hedef: prod’u **bozmadan** güvenliği artırmak.

Tartışmasız maddeler:
- CSP **Report-Only** ile başlar.
- Zorunlu kılmadan önce **≥ 7 gün** ihlal verisi toplayın.
- HSTS kademeli olarak artırılır.
- Geri alma, tek bir config anahtarıyla **< 5 dakika** içinde mümkün olmalı.
- Kapsam önceliği: admin/tenant UI’lar. Player UI ayrı olarak değerlendirilir.

Kanonik politika referansı:
- `docs/ops/csp_policy.md`

Kanonik Nginx include tasarımı (geri alma kolu):
- `docs/ops/snippets/security_headers.conf`
- `docs/ops/snippets/security_headers_report_only.conf`
- `docs/ops/snippets/security_headers_enforce.conf`

---

## Faz 0 — Temel başlıklar (zaten mevcut değilse)

### Değişiklik
Temel başlıkları etkinleştirin:
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `X-Frame-Options: DENY` (savunma-derinlik)

(Zaten her iki snippet içinde de yer alır.)

### Doğrulama```bash
curl -I https://<admin-domain>/
```Beklenen: başlıklar mevcut.

### Geri alma (< 5 dk)
- Include’ı OFF konumuna alın (`security_headers.conf` içinde include’u yorum satırı yapın) ve nginx’i yeniden yükleyin.

---

## Faz 1 — CSP Report-Only (ADMIN/TENANT)

### Değişiklik
Report-only include’u kullanın:
- `security_headers_report_only.conf`, `Content-Security-Policy-Report-Only` ayarlar.

### Doğrulama
1) Başlık mevcut:```bash
curl -I https://<admin-domain>/ | grep -i content-security-policy
```Beklenen:
- `Content-Security-Policy-Report-Only: ...`

2) UI smoke:
- giriş
- tenant listesi
- ayarlar sayfaları
- çıkış

3) **≥ 7 gün** boyunca ihlalleri toplayın:
- tercih edilen: rapor endpoint’i (yapılandırıldıysa)
- yedek: tarayıcı konsolu üzerinden toplama

### Geri alma (< 5 dk)
- Include’ı OFF konumuna alın (include’u yorum satırı yapın) ve nginx’i yeniden yükleyin.

---

## Faz 2 — CSP Enforce

### Kapı (sağlanması şart)
- Report-only **≥ 7 gün** etkin
- İhlaller gözden geçirildi
- Allowlist politikada güncellendi

### Değişiklik
Include’u enforce’a geçirin:
- `security_headers_enforce.conf`, `Content-Security-Policy` ayarlar.

### Doğrulama```bash
curl -I https://<admin-domain>/ | grep -i content-security-policy
```Beklenen:
- `Content-Security-Policy: ...`

UI smoke + hata oranlarını izleyin.

### Geri alma (< 5 dk)
- Include’ı tekrar `security_headers_report_only.conf` dosyasına alın.

---

## Faz 3 — Sıkılaştırma

### Değişiklik
Yaygınlaştırma sırasında süreyle sınırlandırılmış geçici izinleri kaldırın:
- `script-src 'unsafe-inline'` kaldırın (eklendiysse)
- istenirse `connect-src`’yi somut allowlist’e daraltın
- gereksiz host izinlerini kaldırın

### Doğrulama
- Faz 2 ile aynı

### Geri alma (< 5 dk)
- Önceki bilinen-iyi CSP config include’una geri dönün.

---

## Faz 4 — HSTS (staging)

### Değişiklik
Yalnızca staging’de düşük max-age etkinleştirin:
- `max-age=300` (5 dakika)

`security_headers_enforce.conf` içinde:```nginx
add_header Strict-Transport-Security "max-age=300" always;
```### Doğrulama```bash
curl -I https://<staging-admin-domain>/ | grep -i strict-transport-security
```Beklenen:
- `Strict-Transport-Security: max-age=300`

### Geri alma (< 5 dk)
- HSTS satırını yorum satırı yapın ve nginx’i yeniden yükleyin.

---

## Faz 5 — HSTS (prod kademeli artırma)

### Değişiklik (kademeli artırma)
Düşük başlayın ve zamanla artırın:
- 1. Gün: `max-age=300`
- 2. Gün: `max-age=3600`
- 3. Gün: `max-age=86400`
- 2. Hafta+: `max-age=31536000`

**Varsayılan duruş:**
- `includeSubDomains`: HAYIR (doğrulanana kadar)
- `preload`: HAYIR (uzun süreli bir taahhüde hazır olana kadar)

### Doğrulama```bash
curl -I https://<prod-admin-domain>/ | grep -i strict-transport-security
```Beklenen:
- başlık mevcut, doğru max-age

### Geri alma (< 5 dk)
- HSTS satırını kaldırın/devre dışı bırakın ve yeniden yükleyin.

> Not: tarayıcılar HSTS’yi max-age süresi boyunca önbelleğe alabilir. Bu nedenle kademeli olarak artırıyoruz.

---

## Acil durum prosedürü (tek anahtar)

CSP/HSTS giriş yapmayı veya kritik sayfaları bozarsa:
1) `security_headers.conf` include’unu OFF veya report-only konumuna alın.
2) nginx’i yeniden yükleyin.
3) Başlıkları `curl -I` ile doğrulayın.
4) UI smoke’u tekrar çalıştırın.