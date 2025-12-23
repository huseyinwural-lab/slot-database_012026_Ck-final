# Transaction State Machine Contract

Bu doküman, **deposit** ve **withdraw** transactionf;lar1 iein backend taraf1nda tek kaynaktan yfnetilen durum makinesini (state machine) tanmlar. Amafoo: FE/BE drift olmamasf, invalid transition hatalarfnda tek tip error payload ve E2E akffflarfn kolay debug edilebilmesidir.

Kaynak kod referansf:
- `backend/app/services/transaction_state_machine.py`
- `backend/app/models/sql_models.py` (Transaction)

Canonical state alanf: **`Transaction.state`**  
`status` alanf legacy/yardfmci; kanonik durum her zaman `state` czerinden okunmalf.

## 1. Ortak Kavramlar

- **tx_type**: `Transaction.type` (`"deposit"` veya `"withdrawal"`).
- **canonical state**: DB'ye yazflan string (`"created"`, `"requested"`, `"approved"`, `"paid"`, `"payout_pending"`, `"payout_failed"`, `"completed"`, `"failed"`, `"canceled"`, `"rejected"`).
- **alias state**: FE veya harici sistemlerin kullandff, DB'de birebir tutulmayan ama canonical'a map edilen deferler ( ffgu. `"pending_review"`, `"succeeded"`).

### 1.1. Alias Haritasf

```python
STATE_ALIASES = {
    "pending_review": "requested",
    "succeeded": "completed",
}
```

`normalize_state(state)` fonksiyonu:
- `None` veya bof state geldiffnde `"created"` dfner,
- Alias deferleri canonical'a cevfirir,
- Difer tcm string'leri aynen bfakf.

## 2. Deposit State Machine

Mantksal akf:

```text
created -> pending_provider -> completed | failed
```

- **created**
  - Backend taraffndan yeni bir deposit istefi yaratfldffnda baflangfc state.
- **pending_provider**
  - PSP'ye fflem gfnderilmif fakat kesin sonucu henfz bilinmiyor.
- **completed**
  - Deposit kesin bafarfl; oyuncu available bakiyesi artmf.
- **failed**
  - Deposit kesin bafarfsf; bakiyede defigiklik yok.

**Allowed transitions (deposit)**

```python
ALLOWED_TRANSITIONS["deposit"] = {
    "created": ["pending_provider"],
    "pending_provider": ["completed", "failed"],
}
```

## 3. Withdraw State Machine

Withdraw iefleminde iki ana faz vardfr:
- **review** (admin onay/red/cancel),
- **payout** (PSP ccerisine para ffkf ve webhook'lar).

Yfzlf state makinesi:

```text
requested -> approved | rejected | canceled
approved  -> payout_pending | paid
payout_pending -> paid | payout_failed
payout_failed  -> payout_pending | rejected
```

Afamlarf:

- **requested**
  - Oyuncu withdraw istefini olufturmuf, admin review bekleniyor.
- **approved**
  - Admin taraffndan onaylanmf, payout afamfasfna hazfr.
- **rejected**
  - Admin taraffndan reddedilmif, fflem kapandf.
- **canceled**
  - Oyuncu veya sistem taraffndan iptal edilmif.
- **payout_pending**
  - PSP'ye payout isteff gfnderilmif; PSP sonucu (paid/failed) bekleniyor.
- **payout_failed**
  - PSP payout isteffi hata ile dfndf; retry veya reject mcmkfn.
- **paid**
  - Payout kesin bafarfl; para PSP taraffndan oyuncunun harici hesabfna gefmif.

**Allowed transitions (withdrawal)**

```python
ALLOWED_TRANSITIONS["withdrawal"] = {
    "requested": ["approved", "rejected", "canceled"],
    "approved": ["paid", "payout_pending"],
    "payout_pending": ["paid", "payout_failed"],
    "payout_failed": ["payout_pending", "rejected"],
}
```

Bu whitelist difffndaki tcm gefiflmeler **invalid transition** sayflfr.

## 4. Invalid Transition Hata Sfemasf

Tcm gefiflmeler `transition_transaction(tx, new_state)` ccrcinden gefer. Bu fonksiyon, whitelist dfffna ffkfge ealfffda **409** fflaa (**HTTPException**) atar:

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

- `tx_type`: `"deposit"` veya `"withdrawal"`
- `from_state`: normalize edilmif mevcut state
- `to_state`: normalize edilmif hedef state

**Not:** Aynf state'e gefme denemeleri (örn. approved -> approved) **idempotent no-op** olarak kabul edilir, hata atflmaz.

## 5. FE/BE State Badge ve Guard Tablosu

Frontend taraffnda state badge/guard mapping'leri bu canonical state listesine birebir baflanmalf; yeni state eklemek veya defifltirmek icin **fnce bu dokfman** ve `ALLOWED_TRANSITIONS` gcncellenmelidir.

fU an ietkin badge seti ffekildir (Admin Withdrawals ccrf.: `FinanceWithdrawals.jsx`):

```js
STATE_LABELS = {
  requested: 'Requested',
  approved: 'Approved',
  payout_pending: 'Payout Pending',
  payout_failed: 'Payout Failed',
  paid: 'Paid',
  rejected: 'Rejected',
};
```

Bu mapping, backend canonical state setiyle birebir hizadadfr.

## 6. Hangi State'ler Limit / Usage Hesabfnda Saylyor?

Tenant gfnlcfk limit enforcement (TENANT-POLICY-001) affaki kurallara gffre uygular:

- **Deposit gfnlcfk kullanfm**:  
  `type = 'deposit' AND state = 'completed'`
- **Withdraw gfnlcfk kullanfm**:  
  `type = 'withdrawal' AND state IN ('requested', 'approved', 'paid')`

Buna gffre:
- Deposit fail'leri (`state='failed'`) gfnlcfk limiti tfketmez.
- Withdraw `rejected` ve `canceled` iflemeleri gfnlcfk limitte sayffmaz; risk gerffeeklefmedifi ie faaliyetsiz kabul edilir.

Bu sefme hem risk/payout taraffndan **beklenen** davranf3f hem de operasyonel olarak "neden limit doldu" sorusunu kolay aefklanabilir kfllfyor.
