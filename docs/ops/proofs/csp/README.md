# CSP Proofs — P4.3 Phase 2 (Observed Violations)

Amaç: CSP **Report-Only** döneminde toplanan violation’ları **tek formatta** kaydetmek ve
Phase 3 (Enforce) kararını **kanıtlı** hale getirmek.

Bu klasördeki dosyalar **repo’da kalır** (audit/operasyon kanıtı).

---

## 1) Ne zaman oluşturulur?
- CSP Report-Only açıldıktan sonra **günlük** veya **dönemsel** (örn. 2-3 günde bir) rapor.
- En az bir rapor, **7 günün sonunda** “enforce gate” kararından önce zorunlu.

---

## 2) Dosya oluşturma (kopyalama akışı)

### 2.1 Template’i kopyala
Önerilen dosya adı standardı:
- `YYYY-MM-DD__YYYY-MM-DD__<env>.md`

Komut:
```bash
cp docs/ops/proofs/csp/P4.3-Phase2-observed-violations.template.md \
  docs/ops/proofs/csp/$(date -u +%F)__$(date -u +%F)__staging.md
```

> Not: İsterseniz ikinci tarihi dönemin bitiş tarihine göre güncelleyin.

### 2.2 Doldur
- Metadata: env/domain/time window (UTC) + commit/versiyon
- Collection method: console / report endpoint / logs
- Violation table: her satır için action + rationale zorunlu
- Decision record: allowlist eklenecek kaynakların **tam listesi**
- Enforce gate: PASS/FAIL + kritik violation sayısı

---

## 3) PASS kriteri (Phase 2 çıktısı)
Bu raporun “Phase 3’e girdi” sayılması için:
- [ ] Violation tablosu doldurulmuş (sample count + action + rationale var)
- [ ] Allowlist additions bölümü net (tam liste)
- [ ] “Critical violation = 0” gate sonucu yazılmış (PASS/FAIL)

---

## 4) Phase 3 (Enforce) kararına nasıl bağlanır?
- Eğer gate **PASS** ise ve allowlist güncellemesi `docs/ops/csp_policy.md` içine merge edildiyse,
  Phase 3’te `SECURITY_HEADERS_MODE=enforce` geçişi için kanıt hazır demektir.
- Eğer gate **FAIL** ise:
  - action=fix code olan maddeler tamamlanır,
  - gerekiyorsa allowlist güncellenir,
  - yeni bir dönem raporu oluşturulur.
