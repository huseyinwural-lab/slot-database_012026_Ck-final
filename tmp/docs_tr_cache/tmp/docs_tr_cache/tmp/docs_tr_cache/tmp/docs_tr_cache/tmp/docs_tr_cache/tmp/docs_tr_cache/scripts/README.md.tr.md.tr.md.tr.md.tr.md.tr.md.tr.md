# Release Smoke Test Suite

Bu dizin, sürüm doğrulaması için gereken otomatik Uçtan Uca (E2E) smoke testlerini içerir.  
Bu betikler, çalışan bir backend’e karşı kritik iş akışlarını (Growth, Payments, Poker, Risk) doğrular.

## 🚀 Kullanım

### Yerel Geliştirme (Varsayılan Mod)
Varsayılan kimlik bilgileriyle (`admin@casino.com` / `Admin123!`) `http://localhost:8001/api/v1` üzerinde çalışır.```bash
python3 scripts/release_smoke.py
```### CI / Katı Mod (Prodüksiyon Geçidi)
Ortam değişkenlerini zorunlu kılar. Yapılandırma eksikse çıkış kodu 2 ile başarısız olur.```bash
export CI_STRICT=1
export API_BASE_URL="http://127.0.0.1:8001/api/v1"
export BOOTSTRAP_OWNER_EMAIL="ci.admin@example.com"
export BOOTSTRAP_OWNER_PASSWORD="secure_ci_password"

python3 scripts/release_smoke.py
```## ⚙️ Yapılandırma (Ortam Değişkenleri)

| Değişken | Açıklama | Varsayılan |
|---|---|---|
| `CI_STRICT` | `1` ise, gerekli değişkenler eksikse başarısız olur. | `0` |
| `API_BASE_URL` | Backend API URL’si | `http://localhost:8001/api/v1` |
| `BOOTSTRAP_OWNER_EMAIL` | Giriş için Yönetici E-postası | `admin@casino.com` |
| `BOOTSTRAP_OWNER_PASSWORD` | Yönetici Parolası | `Admin123!` |
| `AUTH_RETRY_MAX_ATTEMPTS` | Maksimum giriş yeniden deneme sayısı | `5` |
| `AUTH_RETRY_BASE_DELAY_SEC` | Backoff gecikme başlangıcı (saniye) | `2.0` |

## 📦 Artifact’ler & Loglar

Loglar şuraya kaydedilir: `/app/artifacts/release_smoke/`

- `summary.json`: Makine tarafından okunabilir çalıştırma özeti.
- `*.stdout.log`: Her test çalıştırıcısının standart çıktısı.
- `*.stderr.log`: Hata logları (varsa).

## 🚦 Çıkış Kodları

- `0`: **BAŞARILI** (Tüm testler başarılı)
- `1`: **BAŞARISIZ** (Bir veya daha fazla test başarısız)
- `2`: **YAPILANDIRMA HATASI** (Katı Mod’da eksik ortam değişkenleri)

## 🔒 Güvenlik

- Loglardaki tüm hassas veriler (tokenlar, parolalar) `***REDACTED***` olarak maskelenir.
- CI hattı, sızıntı olmadığından emin olmak için çalıştırma sonrası bir grep kontrolü yapar.