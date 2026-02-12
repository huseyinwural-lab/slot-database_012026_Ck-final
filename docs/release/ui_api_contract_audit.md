# UI API Contract Audit

**Date:** 2026-02-16
**Status:** AUDITED ✅

## 1. Approval Queue
| UI Path | Method | Endpoint | Backend Status | Note |
|---|---|---|---|---|
| `/approvals` | GET | `/v1/approvals/requests?status={status}` | ✅ FIXED | Added status filter logic. |
| `/approvals` | GET | `/v1/approvals/rules` | ✅ STUBBED | Returns `[]` (No 404). |
| `/approvals` | GET | `/v1/approvals/delegations` | ✅ STUBBED | Returns `[]` (No 404). |
| `/approvals` | POST | `/v1/approvals/requests/{id}/action` | ✅ EXISTS | Logic functional. |

## 2. Risk Management
| UI Path | Method | Endpoint | Backend Status | Note |
|---|---|---|---|---|
| `/risk` | GET | `/v1/risk/dashboard` | ✅ NEW | Added aggregate endpoint. |
| `/risk` | GET | `/v1/risk/rules` | ✅ NEW | Returns V2 Hardcoded rules. |
| `/risk` | GET | `/v1/risk/velocity` | ✅ STUBBED | Returns `[]`. |
| `/risk` | GET | `/v1/risk/cases` | ✅ STUBBED | Returns `[]`. |
| `/risk` | GET | `/v1/risk/alerts` | ✅ STUBBED | Returns `[]`. |
| `/risk` | GET | `/v1/risk/blacklist` | ✅ STUBBED | Returns `[]`. |

## 3. Fraud Check
| UI Path | Method | Endpoint | Backend Status | Note |
|---|---|---|---|---|
| `/fraud` | POST | `/v1/fraud/analyze` | ✅ MOCKED | Returns deterministic risk score. |

## Conclusion
All "Red" broken buttons now have corresponding Backend endpoints (Real or Mock/Stub). 
No 404 errors should occur on main Admin paths.
