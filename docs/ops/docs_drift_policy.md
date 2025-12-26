# Docs Drift Policy - Living Documentation

**Status:** ACTIVE
**Owner:** Ops Lead

## 1. Core Principle
**"Code changes are incomplete without Documentation updates."**
Any Pull Request (PR) that modifies the following MUST include a corresponding update to `/app/docs/`:
*   **Financial Flows:** Ledger logic, Payout states, Idempotency.
*   **Operational Tooling:** Script names, parameters, or output formats.
*   **Critical Procedures:** Runbook steps, Rollback criteria, Escalation paths.

## 2. CI/CD Guardrails
The script `/app/scripts/docs_drift_check.py` runs in the CI pipeline.
*   **Broken Links:** Checks if referenced files exist in the repo.
*   **Script Paths:** Verifies that scripts mentioned in Runbooks exist in `/app/scripts/`.
*   **Freshness:** Warns if core docs haven't been reviewed in **90 days**.

## 3. Documentation Ownership
| Document | Owner | Review Frequency |
|---|---|---|
| `go_live_runbook.md` | Ops Lead | Quarterly |
| `bau_governance.md` | Ops Lead | Quarterly |
| `onboarding_pack.md` | Engineering Lead | Monthly |
| `glossary.md` | Product Owner | Ad-hoc |

## 4. Versioning Standard
Every core document must have a metadata header:
```markdown
**Last Reviewed:** YYYY-MM-DD
**Reviewer:** [Name]
```

## 5. Drift Incident
If a runbook fails during an incident because it was outdated:
1.  Sev-2 Incident raised for "Documentation Failure".
2.  Post-mortem focuses on *why* the drift occurred (process failure vs. tooling failure).
3.  Docs Drift Policy is reviewed.
