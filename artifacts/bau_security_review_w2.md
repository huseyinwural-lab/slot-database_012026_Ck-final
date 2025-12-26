# BAU: Week 2 Security Review
**Date:** [T+14 Date]
**Reviewer:** Security Lead

## 1. Waiver Register Status
*Reference: `/app/artifacts/prod_env_waiver_register.md`*

| Secret/Config | Risk Level | Status | Remediation Plan |
|---|---|---|---|
| `STRIPE_SECRET_KEY` | Medium | [ ] Open / [ ] Closed | |
| `STRIPE_WEBHOOK` | High | [ ] Open / [ ] Closed | |
| `ADYEN_KEYS` | High | [ ] Open / [ ] Closed | |

**High Risk Items Remaining:** [Number]

## 2. Prod Access Control Review
- **Admin Users:** [Number]
- **Least Privilege Violations:** [Number]
- **Action Taken:**
  - [User/Role]: [Action]

## 3. Security Action Plan (Next 2 Weeks)
| Task | Owner | Deadline |
|---|---|---|
| Rotate Secrets | DevOps | |
| Review IAM Roles | SecOps | |
