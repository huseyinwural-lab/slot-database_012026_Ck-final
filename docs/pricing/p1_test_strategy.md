# P1 Test Strategy

**Philosophy:** Deterministic Matrix Testing (No Random Data).

## 1. Test Data Management
- **Segments:** Use fixed fixtures: `SEG_INDIV_01`, `SEG_GAL_01`.
- **Prices:** Use integer-friendly base prices (e.g., 100.00) to avoid floating point ambiguity in asserts.

## 2. Scenarios (Matrix)

| Base Price | Segment | Discount Type | Discount Value | Expected Net |
| :--- | :--- | :--- | :--- | :--- |
| 100.00 | INDIVIDUAL | NONE | 0 | 100.00 |
| 100.00 | GALLERY | FLAT | 10.00 | 90.00 |
| 100.00 | GALLERY | PERCENT | 20% | 80.00 |
| 100.00 | ENTERPRISE | TIERED (Tier 1) | 100% (Free) | 0.00 |

## 3. Integration Tests (Postgres)
- **Concurrency:** Simulate 2 requests applying conflicting discounts simultaneously. Verify "Last Write Wins" or "Optimistic Lock" behavior based on policy.
- **State Transitions:** Verify `Quote` -> `Commit` flow maintains discount validity (e.g., discount didn't expire between quote and commit).

## 4. Acceptance Criteria
- All matrix permutations pass.
- Reporting view correctly aggregates `gross` vs `net`.
- No regression in T2 waterfall logic.
