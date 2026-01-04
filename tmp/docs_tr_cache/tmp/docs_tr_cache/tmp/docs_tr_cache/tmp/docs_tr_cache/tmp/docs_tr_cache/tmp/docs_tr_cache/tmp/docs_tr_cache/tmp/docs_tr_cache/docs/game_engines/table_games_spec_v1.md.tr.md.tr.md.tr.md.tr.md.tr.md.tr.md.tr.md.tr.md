# Table Games Spec v1 (BAU W4)

**Status:** APPROVED
**Date:** 2025-12-26

## 1. Roulette (Internal Engine v1)
### Mechanics
- **Variant:** European (Single Zero).
- **RNG:** Standard PRNG seeded by (RoundID + ServerSeed).
- **Bet Types:**
  - Inside: Straight, Split, Street, Corner, Line.
  - Outside: Red/Black, Even/Odd, High/Low, Dozens, Columns.

### Payout Table
| Bet Type | Payout |
|----------|--------|
| Straight | 35:1 |
| Split | 17:1 |
| Red/Black | 1:1 |

### Audit Requirements
- **Snapshot:** `{"winning_number": 17, "bets": [...]}`.
- **Verification:** Hash(Grid) -> Hash(Number).

---

## 2. Dice (Internal Engine v1)
### Mechanics
- **Mode:** Classic Hi/Lo.
- **Range:** 0.00 to 100.00.
- **Player Choice:** "Roll Over X" or "Roll Under X".

### Payout Formula
`Multiplier = (100 - HouseEdge) / WinChance`
- **House Edge:** 1.0% (Configurable via Engine Standards).

---

## 3. Blackjack (Roadmap v1.5)
- **Engine:** Internal state machine required (Deal -> Hit/Stand -> Outcome).
- **Strategy:** Postpone to Sprint 5 due to state complexity. Use Provider for now.

## 4. Decision Matrix
See `table_games_decision_matrix.md`.
