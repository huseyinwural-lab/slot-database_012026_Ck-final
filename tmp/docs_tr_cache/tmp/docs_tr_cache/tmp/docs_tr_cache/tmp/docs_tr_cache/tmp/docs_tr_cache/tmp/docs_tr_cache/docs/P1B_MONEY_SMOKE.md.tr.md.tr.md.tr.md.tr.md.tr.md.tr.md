# P1-B-S: Minimal Money-Loop Smoke (Harici Ortam) — Go/No-Go Kapısı

## Kapsam
Bu smoke, harici Postgres + harici Redis üzerinde **cüzdan/defter (ledger) değişmezlerini (invariants)** en hızlı PSP’siz yol ile doğrular:
- Admin manuel kredi/borç / defter düzeltmesi (PSP/webhook yok)
- İdempotency, `Idempotency-Key` başlığı ile zorunlu kılınır
- Kanıt URL’sizdir (maskelenmiş)

Bu bir **Go/No-Go** kapısıdır. Başarısız olursa, release yok.

---

## Önkoşullar
- P1-B hazırlık kapısı geçer:
  - `GET /api/ready` = 200
  - `dependencies.database=connected`
  - `dependencies.redis=connected`
  - `dependencies.migrations=head` (veya muadili)
- Ortam:
  - `ENV=staging` (veya prod-benzeri)
  - Sıkı davranış için `CI_STRICT=1` önerilir
- Maskeleme kuralları: sırlar ve kimlik bilgileri `***` ile değiştirilmelidir.

---

## Kanonik Endpoint’ler (bu repo)
Bu codebase’de bu smoke için kullanılacak kanonik endpoint’ler şunlardır:

- Hazırlık kapısı:
  - `GET /api/ready`
  - `GET /api/version`

- Oyuncu oluşturma (admin):
  - `POST /api/v1/players`

- Cüzdan + defter snapshot’ları (admin):
  - `GET /api/v1/admin/players/{player_id}/wallet`
  - `GET /api/v1/admin/players/{player_id}/ledger/balance`

- Manuel düzeltme (admin, PSP’siz):
  - `POST /api/v1/admin/ledger/adjust`
    - Body: `{ "player_id": "...", "delta": 100, "reason": "...", "currency": "USD" }`
    - Header: `Idempotency-Key: ...`

---

## Varlıklar & Notasyon
- Oyuncu: `player_id`
- Cüzdan bakiyesi: `wallet_balance`
- Defter (ledger) bakiyesi: `ledger_balance`
- Para birimi: deployment config’iniz farklı değilse varsayılan sistem para birimini (`USD`) kullanın.

**Değişmez (Invariant):** Her işlemden sonra, para birimi kapsamı için `wallet_balance.total_real == ledger_balance.total_real`.

---

## Kanıt Çıktı Şablonu (Denetim Kaydı)
`docs/P1B_SELF_SERVE.md` kanıt şablonuyla aynı yapıyı kullanın:
- Zaman damgası (UTC), ortam, `/api/version`, çalıştıran (maskelenmiş)
- Her komut için: komut + HTTP status + response + exit code

---

## Adım 0 — Hazırlık Kapısı```bash
curl -sS -i http://localhost:8001/api/ready
echo "EXIT_CODE=$?"
curl -sS -i http://localhost:8001/api/version
echo "EXIT_CODE=$?"
```GO: `/api/ready` = 200

NO-GO: 200 olmayan

---

## Adım 1 — Oyuncu Oluşturma
Bu repo’daki kanonik endpoint’i kullanın.```bash
curl -sS -i -X POST http://localhost:8001/api/v1/players \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{ "email":"p1b_smoke_***@example.com", "username":"p1b_smoke_user", "password":"***" }'
echo "EXIT_CODE=$?"
```Yanıttan `player_id` değerini kaydedin.

GO: Geçerli bir `player_id` ile 201/200

NO-GO: 2xx olmayan

---

## Adım 2 — Öncesi Snapshot (Cüzdan + Defter)```bash
# Wallet snapshot
curl -sS -i http://localhost:8001/api/v1/admin/players/${player_id}/wallet \
  -H "Authorization: Bearer ***"
echo "EXIT_CODE=$?"

# Ledger snapshot
curl -sS -i http://localhost:8001/api/v1/admin/players/${player_id}/ledger/balance \
  -H "Authorization: Bearer ***"
echo "EXIT_CODE=$?"
```GO: yanıtlar 200 ve tutarlı

NO-GO: 200 olmayan veya zaten uyumsuzluk var

---

## Adım 3 — Manuel Kredi (İdempotent)
Bir tutar seçin, ör. +100.```bash
curl -sS -i -X POST http://localhost:8001/api/v1/admin/ledger/adjust \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: p1b-credit-001" \
  -d '{ "player_id":"'"${player_id}"'", "delta": 100, "reason":"P1-B-S smoke credit", "currency":"USD" }'
echo "EXIT_CODE=$?"
```Aynı isteği birebir yeniden çalıştırın (aynı `Idempotency-Key`).

GO:
- İlk çağrı: 2xx
- İkinci çağrı: 2xx VE ek delta uygulanmadı (`idempotent_replay=true` veya muadili)
- Son durum: cüzdan ve defter toplamları **yalnızca bir kez** tam olarak **+100** artmış olmalı

NO-GO: çift kredi veya cüzdan/defter uyumsuzluğu

---

## Adım 4 — Manuel Borçlandırma (İdempotent)
Bir tutar seçin, ör. -40.```bash
curl -sS -i -X POST http://localhost:8001/api/v1/admin/ledger/adjust \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: p1b-debit-001" \
  -d '{ "player_id":"'"${player_id}"'", "delta": -40, "reason":"P1-B-S smoke debit", "currency":"USD" }'
echo "EXIT_CODE=$?"
```Aynı isteği aynı `Idempotency-Key` ile yeniden çalıştırın.

GO:
- Tam olarak bir kez uygulandı
- Son durum: bakiyeler **yalnızca bir kez** tam olarak **40** azalmış olmalı
- `wallet_balance.total_real == ledger_balance.total_real`

NO-GO: çift borçlandırma veya uyumsuzluk

---

## Adım 5 — Opsiyonel (Güçlü) DB Kanıtı
Defter olaylarını listelemek için güvenli, yalnızca admin’e açık bir endpoint’iniz varsa şunları kaydedin:
- `p1b-credit-001` için tam olarak bir event
- `p1b-debit-001` için tam olarak bir event

(Endpoint mevcut değilse bu dokümanın kapsamı dışındadır.)

---

## Go / No-Go Özeti
TÜMÜ doğruysa GO:
- `/api/ready` = 200
- Manuel kredi, idempotency replay altında tam olarak bir kez uygulandı
- Manuel borçlandırma, idempotency replay altında tam olarak bir kez uygulandı
- Her adımdan sonra, `wallet_balance.total_real == ledger_balance.total_real`

HERHANGİ BİRİ doğruysa NO-GO:
- ready 200 olmayan
- aynı idempotency key altında mükerrer uygulama
- herhangi bir noktada cüzdan/defter uyumsuzluğu
- replay’ler arasında deterministik olmayan davranış

---

## Takip (bu dokümanın kapsamı dışındadır)
- Webhook + idempotency dahil PSP sandbox akışı (Stripe/Adyen) (P1-B-S2)
- Para çekme hold/approve/paid yaşam döngüsü smoke’u (adjust endpoint’leri tarafından kapsanmıyorsa)

---

## EK: Tek seferde kanıt yakalama (tek yapıştırma)

### Amaç
G0→G4’ü tek seferde çalıştırın, çıktı sırasını deterministik tutun ve tek bir yapıştırma olarak paylaşın.

### Kullanım
1) Harici ortam shell’inizde `BASE_URL` ve `ADMIN_JWT` ayarlayın.
2) Aşağıdaki script’i çalıştırın.
3) Tüm çıktıyı kopyalayın ve bu kanala geri yapıştırın.
4) Paylaşmadan önce kurallara göre yalnızca sırları/token’ları/kimlik bilgilerini maskeleyin.

### Tek seferlik komut (bash)```bash
set -euo pipefail

BASE_URL="${BASE_URL:?set BASE_URL}"
ADMIN_JWT="${ADMIN_JWT:?set ADMIN_JWT}"

# helper: request wrapper
req() { bash -c "$1"; echo; }

echo -e "\n===== G0: /api/ready =====\n"
req "curl -sS -i \"$BASE_URL/api/ready\""

echo -e "\n===== G0: /api/version =====\n"
req "curl -sS -i \"$BASE_URL/api/version\""

echo -e "\n===== G1: POST /api/v1/players =====\n"
# IMPORTANT: prefer canonical payload from this doc.
# Below is a common-safe payload; adjust if validation fails (e.g., username required).
PLAYER_CREATE_RESP="$(curl -sS -i -X POST \"$BASE_URL/api/v1/players\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -d '{"email":"p1b_smoke_'$(date +%s)'@example.com","username":"p1b_smoke_'$(date +%s)'","password":"TempPass!123"}')"
echo "$PLAYER_CREATE_RESP"
echo

# Extract player_id if present (best-effort; works if body contains "id" or "player_id")
PLAYER_ID="$(echo "$PLAYER_CREATE_RESP" | tail -n 1 | sed -n 's/.*"player_id"[[:space:]]*:[[:space:]]*"\([^"]\+\)".*/\1/p')"
if [ -z "${PLAYER_ID:-}" ]; then
  PLAYER_ID="$(echo "$PLAYER_CREATE_RESP" | tail -n 1 | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]\+\)".*/\1/p')"
fi

if [ -z "${PLAYER_ID:-}" ]; then
  echo -e "\n===== STOP: player_id not found (G1 likely FAIL). Paste output as-is for NO-GO evaluation. =====\n"
  exit 0
fi

echo -e "\n===== G2: Wallet before =====\n"
req "curl -sS -i \"$BASE_URL/api/v1/admin/players/$PLAYER_ID/wallet\" -H \"Authorization: Bearer $ADMIN_JWT\""

echo -e "\n===== G2: Ledger before =====\n"
req "curl -sS -i \"$BASE_URL/api/v1/admin/players/$PLAYER_ID/ledger/balance\" -H \"Authorization: Bearer $ADMIN_JWT\""

echo -e "\n===== G3: Credit + replay (Idempotency-Key: p1b-credit-001) =====\n"
req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-credit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":100,"reason":"P1-B-S smoke credit","currency":"USD"}'"

req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-credit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":100,"reason":"P1-B-S smoke credit","currency":"USD"}'"

echo -e "\n===== G4: Debit + replay (Idempotency-Key: p1b-debit-001) =====\n"
req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-debit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":-40,"reason":"P1-B-S smoke debit","currency":"USD"}'"

req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-debit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":-40,"reason":"P1-B-S smoke debit","currency":"USD"}'"

echo -e "\n===== DONE: Paste this entire output (mask tokens only) =====\n"
```### Maskeleme hatırlatması
- Yalnızca şunları maskeleyin: `Authorization: Bearer <token>` → `Authorization: Bearer ***`
- Şunları maskelemeyin: `player_id`, HTTP status kodları, `idempotent_replay`