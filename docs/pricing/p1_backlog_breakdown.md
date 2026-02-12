# P1 Backlog Breakdown: Discount & Segmentation

**Strategy:** Ordered execution (Segment -> Discount -> Reporting).

## P1.1: Segmentation Engine
*Foundation for applying rules.*
- **Ticket 1:** Define `Segment` Enum/Model (e.g., `INDIVIDUAL`, `GALLERY`, `ENTERPRISE`).
- **Ticket 2:** Implement `SegmentResolver`. Input: `TenantID/UserID` -> Output: `Segment`.
- **Ticket 3:** Policy Matrix Base. Map `Segment` -> `PricingConfiguration`.

## P1.2: Discount Logic
*Application of price modifiers.*
- **Ticket 4:** Discount Types Implementation.
    - `FLAT`: Subtract fixed amount.
    - `PERCENTAGE`: Subtract % of base price.
    - `TIERED`: Volume-based (e.g., first 5 free, next 5 at 50%).
- **Ticket 5:** Precedence Rules Engine.
    - Define order: `Base Price` -> `Segment Adjustment` -> `Campaign Discount` -> `Volume Discount`.
    - "Best Price" logic vs "Stacking" logic (Decision: MVP uses Best Price only, no stacking).

## P1.3: Reporting & Audit
*Visibility of financial impact.*
- **Ticket 6:** Ledger Schema Expansion. Add columns: `gross_amount`, `discount_amount`, `net_amount`, `applied_discount_id`.
- **Ticket 7:** NGR (Net Gaming Revenue style) calculation logic.
- **Ticket 8:** Audit Log expansion. Capture *why* a specific price was applied (Traceability).
