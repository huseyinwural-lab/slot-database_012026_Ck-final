# Release Smoke Test Suite

This directory contains the automated End-to-End (E2E) smoke tests required for release validation.
These scripts verify critical business flows (Growth, Payments, Poker, Risk) against a running backend.

## 🚀 Usage

### Local Development (Default Mode)
Runs with default credentials (`admin@casino.com` / `Admin123!`) against `http://localhost:8001/api/v1`.

```bash
python3 scripts/release_smoke.py
```

### CI / Strict Mode (Production Gate)
Enforces environment variables. Fails with exit code 2 if configuration is missing.

```bash
export CI_STRICT=1
export API_BASE_URL="http://127.0.0.1:8001/api/v1"
export BOOTSTRAP_OWNER_EMAIL="ci.admin@example.com"
export BOOTSTRAP_OWNER_PASSWORD="secure_ci_password"

python3 scripts/release_smoke.py
```

## ⚙️ Configuration (Environment Variables)

| Variable | Description | Default |
|---|---|---|
| `CI_STRICT` | If `1`, fails if required vars are missing. | `0` |
| `API_BASE_URL` | Backend API URL | `http://localhost:8001/api/v1` |
| `BOOTSTRAP_OWNER_EMAIL` | Admin Email for Login | `admin@casino.com` |
| `BOOTSTRAP_OWNER_PASSWORD` | Admin Password | `Admin123!` |
| `AUTH_RETRY_MAX_ATTEMPTS` | Max login retry count | `5` |
| `AUTH_RETRY_BASE_DELAY_SEC` | Backoff delay start (seconds) | `2.0` |

## 📦 Artifacts & Logs

Logs are saved to: `/app/artifacts/release_smoke/`

- `summary.json`: Machine-readable execution summary.
- `*.stdout.log`: Standard output of each test runner.
- `*.stderr.log`: Error logs (if any).

## 🚦 Exit Codes

- `0`: **PASS** (All tests succeeded)
- `1`: **FAIL** (One or more tests failed)
- `2`: **CONFIG ERROR** (Missing env vars in Strict Mode)

## 🔒 Security

- All sensitive data (tokens, passwords) in logs are masked as `***REDACTED***`.
- The CI pipeline runs a post-execution grep check to ensure no leakage.
