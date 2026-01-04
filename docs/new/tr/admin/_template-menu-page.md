# <MENÜ BAŞLIĞI> (TR)

**Menü yolu (UI):** `<Sidebar → ...>`  
**Frontend route:** `<örn. /games>`  
**Sadece owner:** Evet/Hayır  

---

## 1) Amaç ve kapsam

(1 paragraf)

---

## 2) Kim kullanır / yetki gereksinimi

- Roller:
  - Platform Owner (super admin): ...
  - Tenant Admin: ...
  - Support / Risk / Finance: ...

---

## 3) Alt başlıklar (varsa)

- ...

---

## 4) Temel akışlar

Uygunsa kapsa:
- Oluşturma (Create)
- Düzenleme (Edit)
- Aktif/Pasif (Enable/Disable)
- Onay/Red (Approve/Reject)
- Import/Export
- Filtre/Arama

---

## 5) Saha rehberi (pratik ipuçları)

- İpuçları (do)
- Anti-pattern (don’t)
- Bu menü **ne zaman kullanılmamalı**

---

## 6) Olası hatalar (semptom → muhtemel neden)

> Minimum 3–8 madde.

1) **Semptom:** ...
   - Muhtemel neden: ...

---

## 7) Çözüm adımları (adım adım)

1) ...
2) ...

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- UI’da nereden doğrulanır

### 8.2 App / container log
- Ne aranır
- Örnek keyword’ler

### 8.3 Audit log
- İlgili event tipleri
- Kanıt için nasıl filtrelenir/export alınır

### 8.4 Database doğrulama (gerekiyorsa)
- Kontrol edilecek tablolar
- Gözlenmesi gereken değişiklik

---

## 9) Güvenlik notları

- Riskli işlemler
- Geri dönüş / recovery notları (riskli aksiyonlarda zorunlu)

---

## 10) İlgili linkler

- Runbook’lar:
  - `/docs/new/tr/runbooks/password-reset.md` (uygunsa)
  - `/docs/new/tr/runbooks/break-glass.md` (uygunsa)
- Sık hatalar:
  - `/docs/new/tr/guides/common-errors.md`
