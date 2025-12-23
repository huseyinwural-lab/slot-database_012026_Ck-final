# Idempotency Standard (Money Path)

Bu dokfman, Admin ve Player yfzeylerinde tcm "para hareketi" if;lemleri if;in kullanddff idempotency standardfnf tanmlar. Amafoo: double-click, network retry, timeout ve webhook replay senaryolarfnda **tek etkili para hareketi** saflamak ve debug/ops ief;leri kolaylaftffrrmaktfr.

Kaynak kod referanslarf:
- FE admin:
  - `frontend/src/pages/FinanceWithdrawals.jsx`
  - `frontend/src/services/moneyActions.js`
  - `frontend/src/services/idempotency.js`
- FE player:
  - `frontend-player/src/pages/WalletPage.jsx`
  - `frontend-player/src/services/moneyActions.js`
- BE:
  - `backend/app/routes/player_wallet.py`
  - `backend/app/routes/finance.py` (withdraw review + payout + webhook)
  - `backend/app/services/psp/mock_psp.py`

## 1. Header Adf

Tcm money-path istekleri ief;in tek standart header ismi:

```http
Idempotency-Key: <string>
```

**Varyasyon yoktur** (`X-Idempotency-Key` vb. kullanlmaz). FE/BE birlikte bu isimde standardize edilmiftr.

## 2. Key Formatlarf

### 2.1. Admin

Admin panelinde tfm para hareketi aksiyonlarf if;in format:

```text
admin:{txId}:{action}:{nonce}
```

- `txId`: Transaction ID (withdrawal if;lemleri ief;in `tx.tx_id` veya benzeri)
- `action`: mantksal aksiyon adf
  - `approve`
  - `reject`
  - `mark_paid`
  - `payout_start`
  - `payout_retry`
  - `recheck`
- `nonce`: aksiyon bazfnda bir kere cretf;ilen, if;lem tamamlanana kadar sabit kalan rastgele defer (uuid4 vb.).

fOrnekler:

```text
Idempotency-Key: admin:tx_123:approve:550e8400-e29b-41d4-a716-446655440000
Idempotency-Key: admin:tx_123:payout_retry:7c3d7b5e-12b3-4c1a-a2ab-9cbbf0d11111
```

### 2.2. Player

Player wallet (deposit / withdraw) aksiyonlarf ief;in format:

```text
player:{playerId}:{action}:{nonce}
```

- `playerId`: oyuncu kimlifi (`player.id`)
- `action`: `deposit` veya `withdraw`
- `nonce`: aksiyon bazfnda bir kere cretf;ilen defer

fOrnekler:

```text
Idempotency-Key: player:plr_42:deposit:b9f9a5c3-22ce-4b57-9d3c-87f0277b0c99
Idempotency-Key: player:plr_42:withdraw:18f490f8-b13f-4f6d-8c76-4b983d824321
```

## 3. UI Davranff (Double-Click & Retry)

### 3.1. Tek kaynaklf key registry

Admin ve player FE taraffnda aff;daki davranff saflayan ortak helper kullanlfr (`moneyActions.js`):

- Her `(scope, id, action)` ef;le ief;in registry entry:
  - `nonce`
  - `createdAt`
  - `status ∈ { idle, in_flight, done, failed }`
- `status='done'` veya `failed` olana kadar **aynf nonce** kullanflfr.
- Double-click sf;rasfnda:
  - `in_flight` durumunda yeni istek gfnderilmez veya _aynf Idempotency-Key_ ile gfnderilir; backend idempotent davrannff.

### 3.2. Retry Politikası

Money-path POST istekleri ief;in retry kurallarf (FE helper cceriden uygular):

- **Retryable:**
  - Network error / timeout (response yok)
  - HTTP 502 / 503 / 504
- **Non-retry:**
  - Tfm 4xx (401/403/409/422 dahil)
  - Difer 5xx (500 vb.)
- Maksimum 2 retry (toplam 3 deneme) ve **her denemede aynf Idempotency-Key** kullanflfr.

## 4. Provider Event Dedupe

Webhook taraffnda PSP event'leri, provider bazfnda ffekilde dedupe edilir:

```text
(provider, provider_event_id)
```

- `provider`: PSP adf (mock veya gercek)
- `provider_event_id`: PSP'nin event kimlifi

Backend, bu fcift (unique constraint) fczerinden gelen her webhook event'ini **bir kere** if;ler; tekrar gelen event'ler idempotent no-op'tur (log'a `FIN_WEBHOOK_REPLAY` gibi bir audit gidebilir).

## 5. 200 No-op / 409 Conflict Semantiff

### 5.1. 200 No-op

Aff;daki durumlarda backend 200/201 dfndfff halde **efektif no-op** olabilir:

- Aynf Idempotency-Key ile tamamen aynf payload tekrar gfnderildiffnde,
- fflem zaten hedef state'te olduffunda ( ffgn. withdrawal zaten `approved` iken tekrar approve denemesi).

Bu durumlarda beklenen davranf:
- Tfketici (UI veya servis) aynf sonucu gfrrf; **ikinci fa para hareketi olmaz**.

### 5.2. 409 Conflict

**409** status, iki ana durumda kullanlfr:

1. **Invalid state transition**  
   Gefel bir transaction ccffin whitelist dfff bir state'e gefirilmek istenmesi:

   ```json
   HTTP 409
   {
     "detail": {
       "error_code": "ILLEGAL_TRANSACTION_STATE_TRANSITION",
       "from_state": "approved",
       "to_state": "requested",
       "tx_type": "withdrawal"
     }
   }
   ```

2. **Idempotency key reuse conflict**  
   Aynf Idempotency-Key ile **farklf payload** gfnderildiffnde:

   ```json
   HTTP 409
   {
     "detail": {
       "error_code": "IDEMPOTENCY_KEY_REUSE_CONFLICT",
       "message": "Idempotency key reused with different request payload.",
       "idempotency_key": "admin:tx_123:approve:..."
     }
   }
   ```

FE taraffnda bu error code'lar **merkezi error map** ( `moneyPathErrorMessage`) ccrcinden ccnf;rlanfr ve aff;daki gibi davranflar tetiklenir:

- `ILLEGAL_TRANSACTION_STATE_TRANSITION`:
  - Mesaj: "fiflemin durumu defiflnmif gffrfnfyor. Liste gf
  - Davranf: Admin Withdrawals listesi auto-refresh.
- `IDEMPOTENCY_KEY_REUSE_CONFLICT`:
  - Mesaj: "Aynf iflemi anahtarf farklf bir istekle kullanfldf. Lftfen sayfay yenileyip tekrar deneyin."
  - Davranf: Uyarf toast + liste yenileme.

## 6. Dzet

- **Tek header ismi**: `Idempotency-Key`
- **Admin formatf**: `admin:{txId}:{action}:{nonce}`
- **Player formatf**: `player:{playerId}:{action}:{nonce}`
- **Provider dedupe**: `(provider, provider_event_id)`
- **Retry**: yalnfzca network/timeout/502/503/504, **aynf key ile**
- **409'lar**: state machine ihlali ve idempotency key reuse confict if;in ayrff error_code'lar.

Bu standarda uymayan yeni endpoint/aksiyon eklenmemelidir; tf m para hareketleri aynf idempotency kural setini paylaflmak zorundadfr.