# BAU Sprint 1: Haftalık Operasyonel Plan

**Dönem:** Canlıya Alım Sonrası 1. Hafta  
**Sahip:** Tek Geliştirici/DevOps  
**Odak:** Kararlılık & Otomasyon

## 1. Rutin Otomasyon (P1)
- [ ] **Günlük Sağlık Özeti:** `hc_010_health.py` dosyasını Cron üzerinden otomatikleştirerek 08:00 UTC’de e-posta/slack ile günlük özet gönder.
- [ ] **Log Rotasyonu:** Diskin dolmasını önlemek için uygulama loglarında `logrotate`’ın aktif olduğunu doğrula.

## 2. KPI & SLO Gösterge Panoları (P1)
- [ ] **Finans Gösterge Panosu:**
  - `Deposit Success Rate` sorgusunu uygula (Son 24s).
  - `Withdrawal Processing Time` sorgusunu uygula (Ort.).
- [ ] **Bütünlük Gösterge Panosu:**
  - `Audit Chain Verification Status` ekle (Son Çalıştırma Sonucu).

## 3. "Acil Durum" Tatbikatları (P2)
- [ ] **DB Geri Yükleme:** 15 dakikalık RTO hedefini doğrulamak için staging ortamına bir geri yükleme gerçekleştir.
- [ ] **Denetim Rehidrasyonu:** Manifest bütünlüğünü doğrulamak için S3’ten rastgele bir günü geçici bir analiz DB’sine geri yükle.

## 4. Engine Standart Bakımı (P2)
- [ ] **Denetim İncelemesi:** 0. Haftadaki tüm `ENGINE_CONFIG_UPDATE` olaylarını incele.
- [ ] **Kural Ayarı:** Eğer herhangi bir "Review Required" olayı yanlış pozitifse, `is_dangerous_change` mantığını ayarla.

## 5. Güvenlik & Erişim
- [ ] **Anahtar Rotasyonu:** İlk `JWT_SECRET` rotasyonunu planla (politika aylık gerektiriyorsa).
- [ ] **Erişim Denetimi:** Tüm aktif oturumları listele ve bayat Admin token’larını geçersiz kıl.