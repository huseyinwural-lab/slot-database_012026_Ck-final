# P1 Discount Schema

## 1. Table: `discounts`
*Catalog of available discounts.*

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `code` | VARCHAR | Unique (e.g., SUMMER_2024) |
| `type` | ENUM | PERCENTAGE, FLAT |
| `value` | DECIMAL | 20.0 (for %) or 10.0 (for flat) |
| `start_at` | TIMESTAMPTZ | Validity Window Start |
| `end_at` | TIMESTAMPTZ | Validity Window End |
| `is_active` | BOOLEAN | Kill switch |

## 2. Table: `discount_rules`
*Binding logic: Who gets what?*

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `discount_id` | UUID | FK -> discounts.id |
| `segment_type` | ENUM | Optional (If null, applies to all) |
| `tenant_id` | UUID | Optional (Specific tenant target) |
| `priority` | INTEGER | Higher wins |

## 3. Usage
- **Query:** Find active rules matching `user.segment` OR `user.tenant_id`.
- **Sort:** By `priority DESC`.
- **Pick:** Top 1.
