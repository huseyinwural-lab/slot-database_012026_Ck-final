# Risk Event Schema

**Version:** 1.0

## 1. Event Structure
All risk events share a common envelope.

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "type": "EVENT_TYPE_ENUM",
  "user_id": "uuid",
  "tenant_id": "uuid",
  "payload": { ... }
}
```

## 2. Event Types & Payloads

### A. BET_PLACED
```json
{
  "type": "BET_PLACED",
  "payload": {
    "amount": 10.00,
    "currency": "USD",
    "game_id": "slot_bonanza",
    "ip": "192.168.1.1"
  }
}
```

### B. WIN_RECORDED
```json
{
  "type": "WIN_RECORDED",
  "payload": {
    "amount": 500.00,
    "currency": "USD",
    "multiplier": 50.0,
    "game_id": "slot_bonanza"
  }
}
```

### C. DEPOSIT_REQUESTED
```json
{
  "type": "DEPOSIT_REQUESTED",
  "payload": {
    "amount": 100.00,
    "method": "stripe",
    "card_fingerprint": "xyz123"
  }
}
```

### D. WITHDRAW_REQUESTED
```json
{
  "type": "WITHDRAW_REQUESTED",
  "payload": {
    "amount": 90.00,
    "method": "crypto",
    "destination_address": "0xabc..."
  }
}
```

### E. LOGIN
```json
{
  "type": "LOGIN",
  "payload": {
    "ip": "192.168.1.1",
    "device_id": "device_hash_123",
    "user_agent": "Mozilla/5.0..."
  }
}
```
