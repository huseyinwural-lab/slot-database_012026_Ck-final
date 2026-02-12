# P1 Discount Observability Validation

**Metric:** `discount_applied_total`

## Validation Steps
1. **Baseline:** Check metric count. (Should be N).
2. **Action:** Create listing with active discount.
3. **Check:** Metric count should be N+1.
4. **Labels:** Verify `discount_type="PERCENTAGE"` and `segment="DEALER"` labels appear.

## Log Verification
- Search for `event="quote_calculated"`
- Confirm `gross`, `net`, `discount_code` fields exist in payload.

**Status:** Ready to verify in Staging.
