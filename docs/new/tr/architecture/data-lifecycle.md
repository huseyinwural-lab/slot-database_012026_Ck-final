# Veri Yaşam Döngüsü (TR)

**Son gözden geçirme:** 2026-01-04  
**Sorumlu:** Ops / Security  

Bu doküman, özellikle audit ve finans açısından verinin zaman içinde nasıl ele alınacağını açıklar.

---

## 1) Soft delete vs hard delete

- Soft delete: kayıt durur, inactive/deleted işaretlenir
- Hard delete: kayıt fiziksel silinir

Öneri:
- finans/audit içeren sistemlerde soft delete tercih edilir

---

## 2) Retention

Tanımla:
- log retention
- audit retention
- backup retention

Legacy:
- `/docs/ops/backup.md`

---

## 3) Purge

Purge:
- owner-only
- audit’li
- restore dışında geri dönüşsüz

---

## 4) Tenant delete etkisi

Tenant delete implement edilmeden önce:
- tenant-scope tablolar listelenmeli
- hangi datanın korunacağı (audit/ledger) belirlenmeli
- silme politikası tanımlanmalı
