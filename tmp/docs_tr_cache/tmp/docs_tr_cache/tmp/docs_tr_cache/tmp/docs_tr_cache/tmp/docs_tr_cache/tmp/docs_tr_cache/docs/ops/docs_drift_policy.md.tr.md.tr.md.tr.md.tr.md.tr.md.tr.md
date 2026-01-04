# Docs Drift Policy - Yaşayan Dokümantasyon

**Durum:** AKTİF
**Sahip:** Operasyon Lideri

## 1. Temel İlke
**"Dokümantasyon güncellemeleri olmadan kod değişiklikleri tamamlanmış sayılmaz."**
Aşağıdakileri değiştiren herhangi bir Pull Request (PR), `/app/docs/` altında karşılık gelen bir güncelleme İÇERMELİDİR:
*   **Finansal Akışlar:** Defter mantığı, Ödeme durumları, İdempotans.
*   **Operasyonel Araçlar:** Betik adları, parametreler veya çıktı formatları.
*   **Kritik Prosedürler:** Runbook adımları, Geri alma kriterleri, Eskalasyon yolları.

## 2. CI/CD Korkulukları
`/app/scripts/docs_drift_check.py` betiği CI hattında çalışır.
*   **Bozuk Bağlantılar:** Referans verilen dosyaların repoda mevcut olup olmadığını kontrol eder.
*   **Betik Yolları:** Runbook’larda bahsedilen betiklerin `/app/scripts/` içinde mevcut olduğunu doğrular.
*   **Güncellik:** Temel dokümanlar **90 gün** içinde gözden geçirilmediyse uyarır.

## 3. Dokümantasyon Sahipliği
| Doküman | Sahip | Gözden Geçirme Sıklığı |
|---|---|---|
| `go_live_runbook.md` | Operasyon Lideri | Üç Aylık |
| `bau_governance.md` | Operasyon Lideri | Üç Aylık |
| `onboarding_pack.md` | Mühendislik Lideri | Aylık |
| `glossary.md` | Ürün Sahibi | Ad-hoc |

## 4. Sürümleme Standardı
Her temel dokümanda bir metadata başlığı bulunmalıdır:```markdown
**Last Reviewed:** YYYY-MM-DD
**Reviewer:** [Name]
```## 5. Dokümantasyon Sapması Olayı
Bir runbook, güncel olmadığı için bir olay sırasında başarısız olursa:
1.  "Dokümantasyon Hatası" için Sev-2 Olayı açılır.
2.  Post-mortem, sapmanın *neden* meydana geldiğine odaklanır (süreç hatası vs. araç hatası).
3.  Docs Drift Policy gözden geçirilir.