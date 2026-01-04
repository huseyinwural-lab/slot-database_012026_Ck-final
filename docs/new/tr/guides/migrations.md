# Upgrade / Migration Rehberi (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Backend Engineering / Ops  

Bu rehber, schema ve code upgrade’lerini güvenli şekilde uygulama sırasını açıklar.

---

## 1) Altın kurallar

1) Migration’ı prod değişikliği gibi ele al
2) Forward-only migration tercih et
3) Her zaman rollback planı olsun (app rollback + DB restore)

---

## 2) Operasyon sırası

Önerilen sıra:

1) Hedef ortamı ve gerekliyse bakım penceresini doğrula
2) Backend image’ını deploy et (veya yeni kodun hazır olduğundan emin ol)
3) Migration çalıştır
4) Smoke check’leri koş

---

## 3) Migration çalıştırma

Tipik komut:

```bash
cd backend
alembic upgrade head
```

Eğer CI/CD migration çalıştırıyorsa:
- loglar kanıt paketi olarak saklanmalı

---

## 4) Migration fail olursa

İlk aksiyonlar:
- rollout’u durdur
- tam migration çıktısını kaydet
- DB bütünlüğünü doğrula

Karar:
- **App rollback**: hata kod seviyesindeyse ve eski versiyon yeni schema olmadan çalışabiliyorsa
- **Hotfix migration**: migration mantığı hızlı düzeltilebiliyorsa
- **Restore**: integrity şüphesi varsa

Legacy DR:
- `/docs/ops/dr_runbook.md`

---

## 5) Tenant bazlı riskler

Multi-tenant riskleri:
- büyük tenant’larda uzun süren migration
- lock contention

Mitigasyon:
- off-peak
- batch backfill
- progress log

---

## 6) Release gate kanıtı

Ekle:
- git SHA
- migration çıktısı
- smoke test sonuçları
