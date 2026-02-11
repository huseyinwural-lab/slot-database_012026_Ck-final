## Player App Contract (Draft)

### Response Envelope
```json
{ "ok": true, "data": {} }
{ "ok": false, "error": { "code": "AUTH_INVALID", "message": "..." } }
```

### Error Codes
- AUTH_INVALID
- AUTH_UNVERIFIED
- VERIFY_EMAIL_REQUIRED
- VERIFY_SMS_REQUIRED
- COMPLIANCE_AGE_REQUIRED
- GAME_LAUNCH_FAILED
- GAME_PROVIDER_DOWN
- PAYMENT_FAILED
- PAYMENT_PENDING
- WALLET_INSUFFICIENT

### Auth
POST /api/v1/auth/player/register
```json
{ "username": "", "email": "", "phone": "", "password": "", "dob": "YYYY-MM-DD", "tenant_id": "default_casino" }
```

POST /api/v1/auth/player/login
```json
{ "email": "", "password": "" }
```

### Verification
POST /api/v1/verify/email/send
POST /api/v1/verify/email/confirm
POST /api/v1/verify/sms/send
POST /api/v1/verify/sms/confirm

### Lobby & Game Launch
GET /api/v1/player/lobby/games
POST /api/v1/player/lobby/launch

### Wallet
GET /api/v1/player/wallet/balance
GET /api/v1/player/wallet/transactions

### Payments
POST /api/v1/player/wallet/deposit
GET /api/v1/payments/:id/status

### Support
POST /api/v1/support/ticket

### Telemetry
POST /api/v1/telemetry/events
