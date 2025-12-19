# P4.3-P2-SCHED-01 — CSP Violation Reporting Schedule (Ops)

Amaç: P4.3 Phase 2 boyunca CSP (Report-Only) violation verisini **düzenli**, **karşılaştırılabilir** ve **kanıta dayalı** şekilde toplamak.

Bu doküman Phase 2 disiplinini standardize eder; Phase 3 (Enforce) adımı ancak bu schedule PASS ise açılır.

---

## 1) Periyot / Cadence

Karar: **2 günde bir proof**.

Hedef set (7 gün): toplam **4 rapor + kapanış**
- D0 (başlangıç) — first snapshot
- D2
- D4
- D6
- D7 (kapanış) — final proof + policy update tamamlanmış olmalı

> Not: D7 kapanışı ayrı bir “final review” olarak görülür; enforce kararı bu kapanıştan sonra verilir.

---

## 2) Sorumluluk

- Sorumlu rol: **Ops on-call** (veya atanmış tek sorumlu rol)
- İsim zorunlu değil; rol bazlı sahiplik yeterli.

---

## 3) Toplama yöntemi (tek standart)

Her rapor şu template ile oluşturulur:
- `docs/ops/proofs/csp/P4.3-Phase2-observed-violations.template.md`

Oluşturma:
```bash
# Önerilen isim: YYYY-MM-DD__YYYY-MM-DD__<env>.md
cp docs/ops/proofs/csp/P4.3-Phase2-observed-violations.template.md \
  docs/ops/proofs/csp/<YYYY-MM-DD__YYYY-MM-DD__staging>.md
```

Doldurma kuralları:
- UTC zaman aralığı zorunlu
- Violation tablosunda her satır için:
  - `sample count`
  - `action` (allowlist / fix code / ignore)
  - `rationale`
  zorunlu

---

## 4) PASS kriteri (her rapor için)

Her raporun gate sonucu:
- **Kritik violation = 0** → **PASS**

Eğer kritik violation varsa:
- Aynı gün içinde aşağıdakilerden en az biri açılır:
  - `action=fix code` (kod/config düzeltme planı)
  - `action=allowlist` (gerekçeli allowlist önerisi)
- Bu durumda rapor **FAIL** sayılır ve bir sonraki rapor döneminde tekrar doğrulanır.

---

## 5) Kapanış (D7)

D7 sonunda aşağıdakilerin hepsi tamam olmalı:
1) D0/D2/D4/D6 raporları + D7 kapanış raporu repo’da mevcut.
2) `docs/ops/csp_policy.md` içindeki **"Observed → Approved additions"** bölümü güncel:
   - Intake (referans proof dosyaları)
   - Approved allowlist (directive bazında)
   - Rejected items
   - Time-boxed exceptions (varsa)
   - **Effective date** atanmış
3) D7 kapanış raporunda gate sonucu:
   - **PASS** (kritik violation = 0)

---

## 6) Phase 3 (Enforce) kararı nasıl bağlanır?

**Phase 3 PR’ı ancak şu koşullarda açılır:**
- Bu schedule’daki raporlar (D0/D2/D4/D6/D7) mevcut
- D7 kapanış raporu **PASS**
- `csp_policy.md` (Approved additions) güncel ve enforce_effective_utc atanmış

Enforce uygulaması staging’de mekanik bir adım olarak yapılır:
- `SECURITY_HEADERS_MODE=report-only` → `enforce`
- rollout restart
- aynı gün UI smoke + header check + kritik violation kontrolü
