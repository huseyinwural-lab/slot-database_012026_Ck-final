# Denetim Saklama ve Arşivleme Runbook'u

## Genel Bakış
Bu runbook, günlük arşivleme, saklama süresine göre silme ve bütünlük zincirlerini doğrulama dahil olmak üzere "Immutable Audit" sisteminin bakımına yönelik prosedürleri tanımlar.

**Gerekli Rol:** Platform Sahibi / DevOps

## 1. Günlük Arşivleme İşi
**Sıklık:** Her gün 02:00 UTC
**Script:** `/app/scripts/audit_archive_export.py`

### Yürütme```bash
# Export yesterday's logs
python3 /app/scripts/audit_archive_export.py --date $(date -d "yesterday" +%Y-%m-%d)
```### Doğrulama
1. `.jsonl.gz` dosyasının yanında `manifest.json` ve `manifest.sig` dosyalarının mevcut olduğunu kontrol edin.
2. `AUDIT_EXPORT_SECRET` kullanarak imzayı doğrulayın.

## 2. Saklama Süresine Göre Temizleme
**Sıklık:** Aylık
**Politika:** "Hot" veritabanında 90 günü tutun, daha eskileri arşivleyin.

### Yürütme
*Şu anda manuel, Task D2 kapsamında otomatikleştirilecek.*```sql
DELETE FROM auditevent WHERE timestamp < NOW() - INTERVAL '90 days';
```**Not:** Bu, `prevent_audit_delete` tetikleyicisinin geçici olarak devre dışı bırakılmasını gerektirir.```sql
DROP TRIGGER prevent_audit_delete;
-- DELETE ...
-- Re-create trigger
```## 3. Zincir Doğrulama (Bütünlük Kontrolü)
Aktif veritabanında hiçbir satırın silinmediğini veya kurcalanmadığını doğrulamak için.

### Script
*Task D1.7 kapsamında yakında*

## 4. Acil Durum: Hukuk İçin Kanıt Dışa Aktarma
Bir düzenleyici belirli logları talep ederse:
1. Filtrelerle Admin UI içindeki `/audit` sayfasını kullanın.
2. "Export CSV" seçeneğine tıklayın.
3. Loglar 90 günden eskiyse CSV + ilgili Günlük Arşiv manifestini sağlayın.