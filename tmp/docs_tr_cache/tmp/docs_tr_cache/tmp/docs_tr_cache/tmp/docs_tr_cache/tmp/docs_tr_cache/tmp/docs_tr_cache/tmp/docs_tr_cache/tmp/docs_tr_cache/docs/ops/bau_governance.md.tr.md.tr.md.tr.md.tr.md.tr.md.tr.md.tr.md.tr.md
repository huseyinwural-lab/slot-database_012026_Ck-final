# BAU Yönetişim Çerçevesi

## 1. İlkeler
- **Önce Güvenlik:** Ticket ve onay olmadan manuel DB düzenlemesi yapılmaz.
- **Her Şeyi Denetle:** Tüm değişiklikler için "Reason" alanı zorunludur.
- **Nöbet (On-Call):** P0 için 15 dk yanıt süresiyle 7/24 kapsama.

## 2. Toplantı Ritmi
- **Günlük Standup (09:30):** Son 24 saatteki olaylar ve dağıtımların gözden geçirilmesi.
- **Haftalık Operasyon Gözden Geçirmesi (Pzt 14:00):** Metrikler, kapasite ve yaklaşan değişikliklerin gözden geçirilmesi.
- **Aylık Güvenlik (1. Perş):** Erişim gözden geçirme, yama yönetimi.

## 3. Değişiklik Yönetimi
- **Standart Değişiklikler:** Ön onaylı (örn. Engine Standard Apply).
- **Normal Değişiklikler:** Eş değerlendirmesi gereklidir (örn. New Feature Flag).
- **Acil Değişiklikler:** Olay sonrası inceleme gereklidir (Break-glass).

## 4. Olay Yönetimi
- **Sev-1 (Kritik):** War room, PagerDuty, Saatlik iletişim.
- **Sev-2 (Yüksek):** Ticket, Günlük iletişim.
- **Sev-3 (Düşük):** Bir sonraki sprint’te düzeltme.