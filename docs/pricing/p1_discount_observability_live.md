# P1 Discount Observability (Live)

**Metrics:**

1. `discount_application_total`
   - Labels: `discount_type` (FLAT/PERCENT), `segment` (INDIVIDUAL/DEALER), `status` (applied/rejected).

2. `pricing_engine_mode`
   - Labels: `version` (v1/v2).
   - Tracks rollout progress.

**Logs:**

```json
{
  "event": "quote_calculated",
  "engine_version": "v2",
  "gross": 100.0,
  "net": 80.0,
  "discount_code": "SUMMER_20",
  "precedence_source": "CAMPAIGN"
}
```
