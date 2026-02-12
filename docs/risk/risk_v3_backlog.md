# Risk V3 Backlog: Behavioral Intelligence

**Focus:** Moving from Rule-Based to Behavioral/ML.

## 1. Behavioral Patterns
- [ ] **Bet Pattern Anomaly:** Detect sudden change in bet size (e.g., $1 -> $100 -> $1).
- [ ] **Game Switching:** Rapidly switching games after losses (Tilt detection).
- [ ] **RTP Deviation:** Win rate > 3 standard deviations from theoretical RTP over N rounds.

## 2. Device & Geo Intelligence
- [ ] **Device Fingerprinting:** Integration with vendors (e.g., FingerprintJS or internal hash).
- [ ] **Geo-Velocity:** Impossible travel (Login UK -> Login China in 5 mins).
- [ ] **VPN Detection:** IP reputation scoring.

## 3. Advanced Actions
- [ ] **Silent Shadowing:** Allow play but shadow ban withdrawals.
- [ ] **Bonus Banishment:** Auto-remove bonus eligibility without blocking account.
