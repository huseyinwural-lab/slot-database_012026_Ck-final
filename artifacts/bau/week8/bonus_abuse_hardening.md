# Bonus Abuse Hardening (BAU W8)

**Status:** ACTIVE
**Focus:** Margin Protection

## 1. Max Bet Guard
*Prevents "High Variance" strategy clearing.*

- **Rule:** While `balance_bonus > 0`: Max Bet = $5.00 (or equivalent).
- **Enforcement:** Game Server rejects bet or Wallet marks it "Wager Exempt".
- **Action:** Warn player on first attempt, void bonus on repeat.

## 2. Game Weighting
*Ensures low-margin games don't clear bonuses easily.*

| Category | Weight | Logic |
|----------|--------|-------|
| Slots | 100% | $1 Bet = $1 Wager |
| Roulette | 10% | $1 Bet = $0.10 Wager |
| Blackjack| 5% | $1 Bet = $0.05 Wager |
| Live | 0% | Excluded |

## 3. Exclusion Logic
- **Restricted Games:** Games with RTP > 98% are automatically excluded from bonus play.
- **Pattern Lock:** Switching from High Volatility (to build balance) to Low Volatility (to clear wager) triggers a `BONUS_ABUSE_SIGNAL`.
