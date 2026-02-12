# P1.1 Segmentation Scope

**Phase:** P1.1 (Segmentation Engine)
**Status:** ACTIVE 🚀
**Goal:** Introduce `INDIVIDUAL` vs `DEALER` differentiation to drive pricing policies.

## 1. Segment Types
Strict Enum (Single Source of Truth):
- `INDIVIDUAL` (Default): Standard user, low limits, Pay-As-You-Go focus.
- `DEALER`: Professional user, high limits, Package access.

## 2. Source of Truth
- **Location:** `users` table.
- **Field:** `segment_type`.
- **Constraint:** NOT NULL (Migration required for existing data).

## 3. Boundaries (What is NOT included)
- Tenant-level overrides (P2).
- Dynamic segmentation based on behavior (P2).
- Multi-segment assignment (Out of scope).

---
**Decision:** All pricing calculations MUST resolve user segment before executing waterfall logic.
