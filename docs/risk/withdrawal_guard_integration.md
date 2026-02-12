# Withdrawal Guard Integration

**Pipeline Stage:** Pre-Processing
**Enforcement:** Mandatory

## 1. Workflow

1.  **User Requests Withdrawal**
    -   Input: Amount, Method.
    
2.  **Risk Guard Check (`RiskService.evaluate_withdrawal`)**
    -   Fetch `UserProfile.risk_score`.
    -   Check Velocity Limits (e.g., max daily limit).
    -   **Decision:**
        -   `PASS`: Proceed to Ledger check.
        -   `FLAG`: Create `ApprovalRequest`, hold transaction.
        -   `BLOCK`: Fail transaction immediately, error `RISK_BLOCK`.

3.  **Ledger Check**
    -   Balance sufficiency (Standard).

4.  **Execution**
    -   If PASS: Send to PSP.
    -   If FLAG: Wait for Admin.

## 2. Integration Code Snippet (Concept)
```python
# In WithdrawalService

async def request_withdrawal(self, user_id, amount):
    # 1. Risk Check
    risk_verdict = await self.risk_service.assess_withdrawal(user_id, amount)
    
    if risk_verdict.action == "BLOCK":
        raise RiskBlockException(risk_verdict.reason)
        
    if risk_verdict.action == "FLAG":
        return await self._create_manual_review_request(user_id, amount)
        
    # 2. Proceed Standard
    return await self._process_auto_withdrawal(user_id, amount)
```
