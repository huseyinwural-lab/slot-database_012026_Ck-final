# Geri Alma Çalışma Kitabı

**Sürüm:** 1.0 (Final)

## Tetikleyiciler (Ne Zaman Geri Alınır)
1. **Kritik Hata:** 10 dakika boyunca sürdürülen >%5 5xx Hata Oranı.
2. **Veri Bütünlüğü:** Denetim Zinciri Doğrulaması Başarısız (`verify_audit_chain.py` hata döndürür).
3. **Finansal Risk:** Çift harcama tespit edilmesi veya büyük Recon Uyumsuzluğu.

## Strateji: İleri Düzeltme vs. Geri Alma
- **Tercih Edilen:** Kod hataları için İleri Düzeltme (Hotfix).
- **Geri Alma:** DB bozulması veya felaket düzeyinde yapılandırma hatası için.

## Prosedür (Geri Alma)

### 1. Trafiği Durdur
- Bakım Modunu etkinleştir.

### 2. Veritabanı Geri Yükleme
*UYARI: WAL günlükleri yeniden oynatılmadıkça son yedekten bu yana oluşan veriler kaybolacaktır.*
1. DB bağlantılarını sonlandır.
2. Pre-Cutover Snapshot’tan geri yükle (bkz. `d4_backup_restore_drill.md`).
3. DB Sağlığını doğrula.

### 3. Uygulama Geri Alma
1. Container Image etiketini `previous-stable` sürümüne geri al.
2. Pod’ları yeniden dağıt.

### 4. Doğrulama
1. Smoke Test Suite’i çalıştır (`scripts/d4_smoke_runner.py` prod için uyarlanmış).
2. `/api/v1/ops/health` kontrol et.

### 5. Trafiği Yeniden Başlat
- Bakım Modunu devre dışı bırak.
- Paydaşları bilgilendir.