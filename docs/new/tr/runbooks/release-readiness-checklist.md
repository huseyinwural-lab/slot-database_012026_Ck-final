# Release Readiness Checklist (TR)

> Not: Yapı ve başlıklar EN ile birebir aynıdır. Sadece dil çevrilmiştir.

---

## 0) Ön Kontrol

**Amaç:** Release kararının tek sorumlusu ve ortam net olsun.

- Release Owner atanmış (Platform Owner)
- Hedef ortam net
- Release zamanı onaylı

**GO:** Owner + ortam net  
**NO-GO:** Belirsizlik

---

## 1) Kimlik Doğrulama & Erişim

**Risk:** Admin erişimi yok / yetkisiz erişim

- Admin login başarılı
- Session/token oluşuyor
- Yetkiler doğru
- Break-glass çalışıyor
- Audit kaydı var

**GO:** Login + audit OK  
**NO-GO:** Login/audit hatası

---

## 2) Tenant & İzolasyon

**Risk:** Yanlış tenant işlemi

- Tenant context net
- Tenant create sadece Platform Owner
- System tenant silinemez
- `tenant_id` izolasyonu doğru

**GO:** İzolasyon sağlam  
**NO-GO:** Yetki ihlali

---

## 3) Oyunlar & Katalog

**Risk:** Yanlış görünürlük / gelir kaybı

- Games listesi çalışıyor
- Enable/disable OK
- VIP kuralı doğru
- Provider bağlantıları OK
- Import gap’leri takipte

**GO:** Görünürlük doğru  
**NO-GO:** Segment/provider hatası

---

## 4) Finans & Çekimler

**Risk:** Para akışı bozulur

- Deposit/withdraw temel akış OK
- Onay kuyruğu çalışıyor
- Ledger tutarlı

**GO:** Finans sağlıklı  
**NO-GO:** Ledger/approval sorunu

---

## 5) Risk & Uyumluluk

**Risk:** Regülasyon ihlali

- KYC çalışıyor
- Fraud kuralları aktif
- Responsible Gaming aktif
- Manuel override audit’leniyor

**GO:** Uyumluluk OK  
**NO-GO:** Kontrol eksik

---

## 6) Gözlemlenebilirlik & Incident

**Risk:** Sorunda müdahale edememe

- Loglara erişim var
- Audit Log erişilebilir
- Incident runbook’lar hazır

**GO:** İzleme hazır  
**NO-GO:** Körlük

---

## 7) Veri & Migrasyonlar

**Risk:** DB açılmaz

- Migration head uyumlu
- DB erişimi OK
- Backup notu mevcut

**GO:** DB sağlıklı  
**NO-GO:** Migration hatası

---

## 8) CI / Release Gate’leri

**Risk:** Kırık build

- CI yeşil
- `docs_smoke` PASS
- Compose acceptance PASS

**GO:** CI temiz  
**NO-GO:** Kırmızı job

---

## 9) Geri Dönüş Planı

**Risk:** Geri alınamaz release

- Frontend rollback
- Backend rollback
- DB rollback politikası
- Kill Switch kriterleri

**GO:** Geri dönüş mümkün  
**NO-GO:** Plan yok

---

## 🔒 Nihai Karar

- ☐ GO
- ☐ NO-GO
