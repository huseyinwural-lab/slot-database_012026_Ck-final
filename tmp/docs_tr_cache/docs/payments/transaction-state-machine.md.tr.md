# Ödemeler İşlem Durum Makinesi

Bu doküman, para yatırma ve para çekme akışları için kanonik işlem durumlarını ve izin verilen geçişleri tanımlar. Ayrıca gerçek bakiye semantiğini (kullanılabilir/bloke) ve tenant günlük limitlerinin kullanımı nasıl saydığını da açıklar.

---

## 0) Kanonik ve UI Etiketleri

Backend kanonik durumları saklar. UI basitleştirilmiş etiketler gösterebilir.

Örnek:
- Para yatırma kanonik: `created -> pending_provider -> completed|failed`
- UI etiketi: genellikle tek bir `pending` aşaması olarak gösterilir (`created` ve `pending_provider` durumlarının ikisini de kapsar)

---

## 1) Kanonik Durum Kümesi

### 1.1 Para yatırma durumları (çekirdek)

- `created`
- `pending_provider`
- `completed`
- `failed`

### 1.2 Para çekme durumları (çekirdek)

- `requested`
- `approved`
- `rejected`
- `canceled`

### 1.3 Ödeme güvenilirliği uzantısı (P0-5)

- `payout_pending`
- `payout_failed`
- `paid`

---

## 2) Para Yatırma Durum Makinesi

### 2.1 Diyagram```text
created -> pending_provider -> completed | failed
```### 2.2 İzin verilen geçişler (kanonik)

- `created → pending_provider`
- `pending_provider → completed | failed`

### 2.3 UI gösterimi

UI erken durumları gruplayabilir:

- `created + pending_provider ⇒ pending` (yalnızca görüntüleme takma adı)

---

## 3) Para Çekme Durum Makinesi

### 3.1 Modern PSP ödeme yolu```text
requested      -> approved | rejected | canceled
approved       -> payout_pending
payout_pending -> paid | payout_failed
payout_failed  -> payout_pending | rejected
```### 3.2 Eski manuel mutabakat yolu```text
approved -> paid
```- Bu yol, Admin **"Mark Paid"** (PSP baypası / manuel mutabakat) için kasıtlı olarak korunmuştur.
- Sağlayıcı entegreli ödemeler için modern PSP ödeme yolu tercih edilmeye devam eder.

### 3.3 İzin verilen geçişler (kanonik)

- `requested → approved | rejected | canceled`
- `approved → paid | payout_pending`
- `payout_pending → paid | payout_failed`
- `payout_failed → payout_pending | rejected`

---

## 4) Geçersiz Geçiş Hata Sözleşmesi

Bir geçiş beyaz listeye alınmamışsa:```json
HTTP 409
{
  "detail": {
    "error_code": "ILLEGAL_TRANSACTION_STATE_TRANSITION",
    "from_state": "approved",
    "to_state": "requested",
    "tx_type": "withdrawal"
  }
}
```Notlar:

- Aynı duruma geçiş (örn. `approved -> approved`) idempotent no-op olarak ele alınır.

---

## 5) Gerçek Bakiye Semantiği (Defter / Cüzdan)

Sistem, aşağıdaki kanonik alanlarla gerçek para bakiyelerini tutar:

- `balance_real_available`
- `balance_real_held`
- `balance_real_total = balance_real_available + balance_real_held`

### 5.1 Para çekme blokeleri ve mutabakat semantiği

`amount` para çekme tutarı olsun.

#### 5.1.1 Para çekme talebinde (`requested`)

- `balance_real_available -= amount`
- `balance_real_held += amount`

Amaç: onay ve ödeme beklenirken fonlar rezerve edilir.

#### 5.1.2 Reddetme (`rejected`) veya iptal (`canceled`) durumunda

- `balance_real_available += amount`
- `balance_real_held -= amount`

Amaç: rezerve edilen fonları tekrar kullanılabilir bakiyeye serbest bırakmak.

#### 5.1.3 Ödeme mutabakatında (`paid`)

- `balance_real_held -= amount`
- `balance_real_available` değişmeden kalır

Amaç: rezerve edilen fonlar sistemden çıkar (ödeme tamamlandı). Kanonik defter olayı `withdraw_paid` olup tam olarak bir kez yazılır.

### 5.2 Para yatırma semantiği

Para yatırmalar, yalnızca nihai tamamlanmada kullanılabilir bakiyeyi artırır:

- `completed` durumunda:
  - `balance_real_available += amount`

Ara sağlayıcı bekleme durumları, açıkça tasarlanmadıkça bakiyeyi değiştirmez (mevcut sözleşme: ara bakiye hareketi yok).

---

## 6) Tenant Günlük Limit Sayımı (TENANT-POLICY-001)

Tenant günlük politika uygulaması, kullanımı kanonik durumlara göre sayar.

### 6.1 Para yatırma günlük kullanımı

Şu para yatırmaları say:

- `type = "deposit"`
- `state = "completed"`

### 6.2 Para çekme günlük kullanımı

Şu para çekmeleri say:

- `type = "withdrawal"`
- `state IN ("requested", "approved", "paid")`

Notlar:

- `failed`, `rejected`, `canceled` günlük kullanıma dahil edilmez.
- Bu seçim, yukarıdaki kanonik durum kümesiyle uyumludur ve TENANT-POLICY-001 tarafından uygulanır.

Uygulama notu: TENANT-POLICY-001 uygulamasının bu exact tabloyu takip etmesi beklenir; buradaki herhangi bir değişiklik hem uygulamayı hem de testleri güncellemelidir.

---

## 7) FE/BE Hizalama Gereksinimleri

Yeni bir durum eklerken:

1. Backend `ALLOWED_TRANSITIONS` (işlem durum makinesi) güncelle,
2. Bu dokümanı güncelle,
3. FE rozet eşlemesini ve aksiyon korumalarını güncelle (Admin/Tenant/Player yüzeyleri),
4. Testleri ekle veya güncelle (unit + uygun olduğunda E2E).

---

## 8) Kanıt Komutları (Sprint 1 P0)

**Tenant politika limitleri:**```bash
cd /app/backend
pytest -q tests/test_tenant_policy_limits.py
```**Para akışı E2E:**```bash
cd /app/e2e
yarn test:e2e tests/money-path.spec.ts
```
