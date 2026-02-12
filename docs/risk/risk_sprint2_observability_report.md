# Risk Sprint 2 Observability Report

**Status:** ACTIVE
**Date:** 2026-02-16

## 1. Metrics Implemented (Prometheus)
- `game_bets_total{status="throttled"}`: Tracks requests blocked by velocity limits.
- `risk_score_updates_total`: Tracks frequency of score changes.
- `risk_blocks_total`: Tracks hard blocks (Withdrawal/Bet).
- `risk_flags_total`: Tracks soft flags (Manual Review).

## 2. Metrics Implemented (Internal Service)
- `MetricsService.risk_blocks`
- `MetricsService.risk_flags`
- `MetricsService.risk_score_updates`
- Exposed via `GET /api/v1/admin/reports/system` (Hypothetical endpoint for internal dashboard).

## 3. Logs
- **Throttling:** `WARNING Bet Throttled: user={id} level={level} count={n} limit={max}`
- **Score Update:** `INFO Risk score updated: user={id} score={new} level={level}`
- **Override:** Audited in `risk_history` table.
