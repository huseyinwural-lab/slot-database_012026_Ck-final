# Ödemeler İdempotensi Sözleşmesi

Bu doküman, tüm para-yolu aksiyonları (yatırma/çekme/ödeme/recheck) ve ödeme webhook’ları için kanonik idempotensi sözleşmesini tanımlar.

## 0) Terminoloji

- **Para-yolu aksiyonu**: gerçek bakiyeleri hareket ettirebilen veya bir finansal işlemi oluşturup/geçiş yaptırabilen bir API çağrısı.
- **İdempotensi**: aynı isteğin tekrarlanması yinelenen etkiler oluşturmamalıdır (çifte tahsilat, çifte defter kaydı, çifte durum geçişi).
- **Dedupe anahtarı**: tekrarları tespit etmek için kullanılan kararlı bir tanımlayıcı (istemci idempotensi anahtarı, sağlayıcı event id, defter event idempotensi anahtarı).

---

## 1) İdempotensi Başlığı (İstemci → API)

### 1.1 Kanonik başlık adı

- **`Idempotency-Key`**, FE/BE genelinde kullanılan tek standart başlıktır.

Alternatifler desteklenmez (örn. `X-Idempotency-Key`).

### 1.2 Zorunlu vs legacy uç noktalar

**Hedef sözleşme (P0):**
- Tüm para-yolu *create/action* uç noktaları `Idempotency-Key` gerektirmek ZORUNDADIR.
- Eksik anahtar `400 IDEMPOTENCY_KEY_REQUIRED` döndürmelidir.

**Mevcut durum:**
- Yeni kritik uç noktalar (payout / recheck ve tüm yeni para aksiyonları) bu gerekliliği uygular.
- Bazı legacy uç noktalar hâlâ eksik anahtarları kabul ediyor olabilir (best-effort idempotensi). Bunlar kademeli olarak hedef sözleşmeye sertleştirilecektir.

> Pratik kural: Bir uç nokta bakiye/defter değişikliklerine neden olabiliyorsa, hedef durum **Idempotency-Key zorunlu** şeklindedir.

---

## 2) Kanonik Anahtar Formatları (FE → BE)

### 2.1 Admin aksiyonları

Format:```text
admin:{txId}:{action}:{nonce}
```- `txId`: çekim işlem kimliği
- `action` (kanonik küme):
  - `approve`
  - `reject`
  - `mark_paid` (legacy manuel mutabakat)
  - `payout_start`
  - `payout_retry`
  - `recheck`
- `nonce`: her `(txId, action)` denemesi için bir kez üretilir ve istek sonuçlanana kadar (başarı/başarısızlık) kalıcı olarak saklanır.

### 2.2 Oyuncu aksiyonları

Format:```text
player:{playerId}:{action}:{nonce}
```- `action` (kanonik küme):
  - `deposit`
  - `withdraw`

---

## 3) UI Davranışı (Çift tıklama, Yeniden deneme)

### 3.1 Devam eden istek kilitlemesi

Aynı `(scope, id, action)` için:

- İstek devam ederken aksiyon butonunu devre dışı bırakın.
- Birden fazla tıklamanın aynı nonce’u yeniden kullanmasını sağlayın → aynı `Idempotency-Key`.
- Tamamlandığında (başarı/başarısızlık), kilidi kaldırın.

### 3.2 Yeniden deneme politikası

Bir yeniden deneme, birebir aynı `Idempotency-Key` değerini yeniden kullanmak ZORUNDADIR.

**Yeniden denenebilir:**
- ağ hataları / zaman aşımları
- 502, 503, 504

**Yeniden denenemez:**
- tüm 4xx (özellikle 401, 403, 409, 422)
- diğer 5xx (aksi açıkça kararlaştırılmadıkça)

**Önerilen varsayılanlar:**
- maksimum yeniden deneme: 2
- backoff: küçük deterministik gecikmeler (UI akışlarında uzun üstel beklemelerden kaçının)

---

## 4) Sunucu Semantiği (201/200 no-op, 409 conflict)

### 4.1 Başarılı ilk create/action

- İlk kez create/action tipik olarak **201 Created** (veya action uç noktaları için 200 OK) döndürür.
- Sunucu tek kanonik etkiyi gerçekleştirir:
  - işlem oluşturma / durum geçişi
  - defter (ledger) olayı/olayları yazma
  - bakiyeleri güncelleme

### 4.2 Replay (aynı Idempotency-Key + aynı payload)

- Daha önce oluşturulmuş kaynak/sonuç ile 200 OK döndürmek ZORUNDADIR.
- No-op olmalıdır (yeni işlem satırı yok, yinelenen defter kaydı yok, ekstra durum geçişi yok).

### 4.3 Conflict (aynı Idempotency-Key + farklı payload)

- Şunlarla birlikte **409 Conflict** döndürmek ZORUNDADIR:```json
{
  "error_code": "IDEMPOTENCY_KEY_REUSE_CONFLICT"
}
```- Yan etkilere izin verilmez.

### 4.4 Geçersiz durum makinesi geçişleri

- Şunlarla birlikte **409 Conflict** döndürmek ZORUNDADIR:```json
{
  "error_code": "INVALID_STATE_TRANSITION",
  "from_state": "...",
  "to_state": "...",
  "tx_type": "deposit|withdrawal"
}
```- Yan etkilere izin verilmez.

---

## 5) Sağlayıcı Replay Dedupe (Webhook/Olay Seviyesi)

### 5.1 Kanonik dedupe anahtarı

Sağlayıcı webhook’ları şu şekilde deduplikasyon yapmak ZORUNDADIR:```text
(provider, provider_event_id)
```- Belirli bir `(provider, provider_event_id)` ile gelen ilk webhook kanonik etkiyi üretir.
- Herhangi bir tekrar (replay) 200 OK döndürmeli ve no-op olmalıdır.

---

## 6) Webhook İmza Güvenliği (WEBHOOK-SEC-001)

Bu bölüm, webhook deduplikasyonundan önce çalışması ZORUNLU olan güvenlik kapısını tanımlar.

### 6.1 Gerekli başlıklar```http
X-Webhook-Timestamp: <unix-seconds>
X-Webhook-Signature: <hex>
```### 6.2 İmzalı payload```text
signed_payload = f"{timestamp}.{raw_body}"
signature      = HMAC_SHA256(WEBHOOK_SECRET, signed_payload).hexdigest()
```- `raw_body`, ayrıştırılmış bir JSON’un yeniden serileştirilmesi değil, ham istek gövdesidir (bytes).
- `WEBHOOK_SECRET`, environment/secret store üzerinden yapılandırılır.

### 6.3 Hata semantiği

- Zaman damgası/imza eksik → `400 WEBHOOK_SIGNATURE_MISSING`
- Zaman damgası geçersiz veya tolerans penceresi dışında (±5 dakika) → `401 WEBHOOK_TIMESTAMP_INVALID`
- İmza uyuşmazlığı → `401 WEBHOOK_SIGNATURE_INVALID`

### 6.4 Sıralama: imza kapısı → dedupe

Webhook işleme sırası:

1. İmzayı doğrula (geçersizse erken reddet)
2. `(provider, provider_event_id)` ile replay deduplikasyonu yap
3. Kanonik durum/defter etkilerini uygula (tam olarak bir kez)

---

## 7) Defter-Seviyesi İdempotensi (Gerçek Para Güvenliği)

Belirli defter olayları, mantıksal sonuç başına en fazla bir kez yazılmak ZORUNDADIR.

**Örnek: `withdraw_paid`**

- Bir çekim, payout başarısı ile `paid` durumuna ulaştığında, bir `withdraw_paid` defter olayı tam olarak bir kez yazılmak ZORUNDADIR.
- Replay’ler (istemci yeniden denemeleri, webhook replay’leri) ek `withdraw_paid` olayları üretmemelidir.
- Koruma, şu kombinasyonla uygulanır:
  - istemci `Idempotency-Key`
  - sağlayıcı `(provider, provider_event_id)` dedupe
  - defter olayı idempotensi anahtarları

---

## 8) Kanıt Komutları (Sprint 1 P0)

**Webhook güvenlik testleri:**```bash
cd /app/backend
pytest -q tests/test_webhook_security.py
```**Tenant politika limitleri:**```bash
cd /app/backend
pytest -q tests/test_tenant_policy_limits.py
alembic heads
alembic upgrade head
```**Para yolu E2E (önceden stabilize edildi):**```bash
cd /app/e2e
yarn test:e2e tests/money-path.spec.ts
```---

## 9) Tek satırlık kapanış

WEBHOOK-SEC-001, TENANT-POLICY-001, IDEM-DOC-001 ve TX-STATE-001 birlikte, para-yolu idempotensisini, webhook güvenliğini, günlük limit kapılamasını ve işlem durum makinesi sözleşmelerini tek bir doğruluk kaynağı olarak tanımlar ve kanıtlar (kod + testler + dokümanlar).