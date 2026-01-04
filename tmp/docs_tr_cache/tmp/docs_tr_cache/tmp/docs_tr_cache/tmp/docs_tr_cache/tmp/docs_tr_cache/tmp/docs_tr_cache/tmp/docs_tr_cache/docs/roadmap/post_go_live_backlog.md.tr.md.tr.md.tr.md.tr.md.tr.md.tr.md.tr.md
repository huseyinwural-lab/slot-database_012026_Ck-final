# Canlıya Geçiş Sonrası Backlog (Stabilizasyon Aşaması)

**Durum:** P1 (Sonraki Sprintler)
**Sahip:** Ürün & Operasyon

## 1. İzleme & İnce Ayar
- [ ] **Alarm İnce Ayarı:** W1 sonrası alarm gürültüsünü gözden geçir. 5xx ve gecikme için eşikleri ayarla.
- [ ] **DB Performansı:** W2 yükü sonrası yavaş sorguları (pg_stat_statements) analiz et. İndeksler ekle.
- [ ] **Kuyruk Optimizasyonu:** Gecikme varsa Mutabakat/Arşivleme için worker eşzamanlılığını ayarla.

## 2. Entegrasyonlar
- [ ] **Canlı Sağlayıcılar:** Gerçek Ödeme Sağlayıcılarını (Stripe/Adyen Canlı Mod) tek tek aktive et.
- [ ] **Oyun Aggregator’ı:** Dahili mock’u değiştirerek gerçek oyun sağlayıcısını (Evolution/Pragmatic) entegre et.

## 3. Dolandırıcılık & Risk
- [ ] **Hız Kuralları:** Gerçek suistimal örüntülerine göre para yatırma limitlerini sıkılaştır.
- [ ] **Bonus Suistimali:** Cihaz parmak izi (device fingerprinting) mantığını uygula (tamamen aktif değilse).

## 4. Uyumluluk (30. Gün+)
- [ ] **Harici Denetim Hazırlığı:** Harici denetçiler için tam aylık denetim dökümünü üret.
- [ ] **GDPR/KVKK:** "Unutulma Hakkı"nı otomatikleştir (Veri Anonimleştirme script’i).

## 5. Özellik İyileştirmeleri
- [ ] **Gelişmiş CRM:** Segment bazlı bonus hedefleme.
- [ ] **Affiliate Portalı:** Affiliate’ler için self-servis dashboard.