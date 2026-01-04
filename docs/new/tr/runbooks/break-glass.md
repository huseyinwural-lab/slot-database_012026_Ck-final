# Break-glass (TR) — Runbook

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Security  

Break-glass, normal erişim yolları çalışmadığında yönetim kontrolünü geri kazanmak için kullanılan kontrollü prosedürdür.

---

## 0) Ne zaman kullanılır?

Sadece şu durumlarda:
- Hiçbir platform owner (super admin) login olamıyor
- Tüm admin’ler lockout olmuş / silinmiş
- Kritik prod incident’te standart yollar bloklu ve acil mitigasyon gerekiyor

Kolaylık için break-glass kullanılmaz.

---

## 1) Onay ve kontroller

Önerilen minimum kontroller:
- 2 kişi onayı (Ops + Security/Engineering)
- Zaman sınırı (time-bounded)
- Zorunlu incident/ticket referansı

Kaydet:
- kim onayladı
- neden
- başlangıç/bitiş timestamp
- yapılan net aksiyonlar

---

## 2) Prosedür

### 2.1 Hedef sonucu belirle
Tam olarak birini seç:
- A) İlk Platform Owner admin’i oluştur
- B) Var olan admin’in şifresini sıfırla
- C) Disabled admin’i tekrar aktif et

### 2.2 Uygula (DB seviyesinde, son çare)

> Deploy’a göre değişir. DB erişimi için internal yöntemlerinizi kullanın (bastion/VPN).

Genel kural:
- Normal erişimi geri getirecek **minimum değişiklik** yap.
- System tenant’ı asla silme.

### 2.3 Break-glass erişimini geri al
- Geçici credential’ları kaldır
- Geçici network erişimini kaldır
- Exposure şüphesinde secret rotation yap

---

## 3) Kanıt (audit-ready)

### 3.1 UI kanıtı
- System → Audit Log export (zaman aralığı)

### 3.2 Backend log
- İlgili backend log satırlarını sakla (`request_id` varsa dahil)

### 3.3 DB kanıtı
- Değişen satırlar için before/after snapshot al:
  - `adminuser`
  - `tenant` (dokunulduysa)

---

## 4) Geri dönüş / recovery

- Yanlış kullanıcı oluşturulduysa veya yanlış tenant değiştiyse: admin’i hemen disable et ve incident raporu üret.
- Credential leak şüphesi varsa: ilgili secret’ları rotate et.

---

## 5) Post-mortem checklist

- [ ] Root cause yazıldı
- [ ] Audit kanıtı üretildi
- [ ] Permission review yapıldı
- [ ] Önleyici fix için backlog maddesi açıldı

