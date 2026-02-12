# Provider Security Matrix

**Phase:** Faz 6A
**Focus:** Pragmatic Play Integration

## 1. Authentication & Integrity
| Layer | Mechanism | Status |
|-------|-----------|--------|
| **Transport** | HTTPS (TLS 1.2+) | Mandatory |
| **Identity** | HMAC-SHA256 Signature | **P0** (Must verify on every request) |
| **Source** | IP Whitelist | **P1** (Configurable middleware) |
| **Replay** | Nonce / Timestamp check | **P2** (If supported by protocol) |

## 2. Fraud Prevention (Internal)
| Threat | Mitigation | Implementation |
|--------|------------|----------------|
| **Balance Manipulation** | Signature Validation | Adapter `validate_request` |
| **Bet Spam** | Risk Layer Throttling | `RiskService` integration |
| **Double Spend** | DB Unique Constraint | `(provider, provider_event_id)` index |
| **Bonus Abuse** | Wagering Contribution | `GameEngine` maps game type to contribution % |

## 3. Risk Layer Integration
- **Checkpoint:** Before any financial DB lock.
- **Action:**
    -   `LOW/MEDIUM`: Pass.
    -   `HIGH`: Throttle aggressivley.
-   **Latency Budget:** Risk check must complete in < 5ms.
