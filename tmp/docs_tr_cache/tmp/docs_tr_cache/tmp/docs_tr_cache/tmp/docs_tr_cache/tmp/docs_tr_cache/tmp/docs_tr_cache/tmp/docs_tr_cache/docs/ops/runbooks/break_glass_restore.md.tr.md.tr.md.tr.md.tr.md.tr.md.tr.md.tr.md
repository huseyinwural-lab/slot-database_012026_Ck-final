# Break-Glass Geri Yükleme Çalışma Kılavuzu

**Sürüm:** 1.0 (BAU)
**Hedef RTO:** 15 Dakika

## 1. Veritabanı Geri Yükleme
**Senaryo:** Birincil veritabanı bozulması veya kaybı.

1.  **Anlık Görüntüyü Bul:**
    S3 `casino-backups` içinde en güncel `backup-YYYY-MM-DD-HHMM.sql.gz` dosyasını bulun.
2.  **Uygulamayı Durdur:**
    `supervisorctl stop backend` (yeni yazmaları engelleyin).
3.  **Geri Yükleme:**```bash
    aws s3 cp s3://casino-backups/latest.sql.gz .
    gunzip -c latest.sql.gz | psql "$DATABASE_URL"
    ```4.  **Doğrula:**
    `player`, `transaction`, `auditevent` için satır sayılarını kontrol edin.

## 2. Denetim Yeniden Doldurma
**Senaryo:** Denetim tablosu kırpılmış veya soruşturma için > 90 gün günlükleri gerekli.

1.  **Arşivi Bul:**
    S3 `casino-audit-archive` içinde `audit_YYYY-MM-DD_partNN.jsonl.gz` dosyasını bulun.
2.  **Geri Yükleme Aracını Çalıştır:**```bash
    python3 /app/scripts/restore_audit_logs.py --date YYYY-MM-DD --restore-to-db
    ```3.  **Doğrula:**
    Araç, İmzayı ve Hash’i otomatik olarak doğrulayacaktır.

## 3. Tatbikat Geçmişi
- **2025-12-26:** Tatbikat gerçekleştirildi. Süre: 4 dk 30 sn. Durum: BAŞARILI.