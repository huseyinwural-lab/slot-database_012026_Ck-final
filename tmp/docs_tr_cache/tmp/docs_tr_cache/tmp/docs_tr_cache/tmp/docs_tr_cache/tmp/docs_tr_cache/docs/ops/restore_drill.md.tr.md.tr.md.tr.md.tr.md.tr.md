# Geri Yükleme Tatbikatı (P3.2) - Tam Geri Yükleme Egzersizi

Amaç: yedeklerin **gerçekten geri yüklenebilir** olduğunu periyodik olarak kanıtlamak.

> Bunu önce üretim olmayan bir ortamda yapın.

## Ön Koşullar
- En az bir adet güncel yedek dosyanız var:
  - `backups/casino_db_YYYYMMDD_HHMMSS.sql.gz`
- Hedef ortamda kesinti süresini göze alabiliyorsunuz.

## Adımlar

### 1) Yedek bütünlüğünü doğrulayın
- Dosyanın var olduğundan ve boş olmadığından emin olun.
- İsteğe bağlı: gzip bütünlüğünü doğrulamak için `gunzip -t <file>`.

### 2) Yazma trafiğini durdurun
- Geri yükleme sırasında yazmaları önlemek için stack’i (veya en azından backend’i) durdurun.

### 3) Geri yükleme
Repo kök dizininden:```bash
./scripts/restore_postgres.sh backups/casino_db_YYYYMMDD_HHMMSS.sql.gz
```### 4) Backend’i yeniden başlatın```bash
docker compose -f docker-compose.prod.yml restart backend
```### 5) Doğrulama
- Sağlık:
  - `curl -fsS http://127.0.0.1:8001/api/health`
  - `curl -fsS http://127.0.0.1:8001/api/ready`
- Sürüm:
  - `curl -fsS http://127.0.0.1:8001/api/version`
- Giriş kontrolü:
  - `POST /api/v1/auth/login` (bilinen admin kimlik bilgilerini kullanın)

### 6) Sonuçları kaydedin
Tatbikatı basit bir değişiklik günlüğüne kaydedin:
- Tarih/saat
- Yedek dosya adı
- Geri yükleme süresi
- Karşılaşılan sorunlar
- Sonraki aksiyonlar

## Önerilen sıklık
- Staging: aylık
- Production: üç ayda bir (veya büyük şema değişikliklerinden sonra)

---

## Kanıt Şablonu (kanonik)

Kanonik şablon:
- `docs/ops/restore_drill_proof/template.md`

Yeni bir kanıt dosyası oluşturun:
- `docs/ops/restore_drill_proof/template.md` → `docs/ops/restore_drill_proof/YYYY-MM-DD.md`

Minimum kanıt gereksinimleri:
- tarih/saat + ortam
- yedek artefakt adı
- geri yükleme komutu çıktısı
- doğrulama çıktıları:
  - `GET /api/ready` (200)
  - `GET /api/version` (beklenen)
  - temel DB kontrolü (tenant sayısı, admin var, migrations head)

## Kanıt Kaydı

Tatbikatı tamamladıktan sonra, kopyalayarak yeni bir kanıt dosyası oluşturun:

- `docs/ops/restore_drill_proof/template.md` → `docs/ops/restore_drill_proof/YYYY-MM-DD.md`

Tatbikat sırasında kullanılan komutları ve çıktıları birebir (aynı şekilde) bunun içine doldurun (gizli bilgiler/tokenlar maskelensin).
Bir tatbikat, yalnızca `/api/health`, `/api/ready`, `/api/version`, owner yetenekleri ve UI smoke testlerinin tamamı geçtiğinde **PASS** sayılır.

### Redaksiyon Kuralları (uyulması zorunlu)

Kanıt dosyalarını commit etmeden önce:

- Tüm bearer tokenlarını `Bearer ***` ile değiştirin.
- Gizli anahtarları ve parolaları kaldırın veya maskeleyin (`*****`).
- Kimlik bilgileri içeren tam connection string’leri yapıştırmayın.
- Loglar header içeriyorsa `Authorization`, `Cookie` ve `X-Api-Key` benzeri tüm değerleri redakte edin.