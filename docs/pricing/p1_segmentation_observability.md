# P1 Segmentation Observability

**Goal:** Slice metrics by `segment_type` to understand business performance.

## 1. Metric Labels Update
Update `pricing_commit_total` and `pricing_allocation_total`.

**New Label:** `segment`
- Values: `individual`, `dealer`

### Example Prometheus Query
```promql
sum(rate(pricing_allocation_total{segment="dealer", type="PAID"}[5m])) 
vs 
sum(rate(pricing_allocation_total{segment="individual", type="PAID"}[5m]))
```

## 2. Logs
Context extraction middleware must inject `segment` into structured logs.

```json
{
  "trace_id": "abc-123",
  "user_id": "u-999",
  "segment": "DEALER",
  "action": "quote",
  "verdict": "FREE"
}
```

## 3. Alerts
- **Anomaly:** If `DEALER` segment free quota rejection rate spikes (Config error?).
- **Business:** If `INDIVIDUAL` segment starts consuming Packages (Logic leak).
