# P1 Segmentation Schema

**Objective:** Define data model changes for Segmentation.

## 1. Database Schema (`users` table)

| Column | Type | Constraints | Default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `segment_type` | VARCHAR / ENUM | NOT NULL | 'INDIVIDUAL' | Indexed for reporting |

## 2. Audit Log Schema (`user_segment_history`)

| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | FK -> users.id |
| `old_segment` | VARCHAR | Nullable (for initial creation) |
| `new_segment` | VARCHAR | NOT NULL |
| `changed_by` | UUID | Admin ID |
| `change_reason` | TEXT | Mandatory for manual changes |
| `created_at` | TIMESTAMPTZ | |

## 3. Implementation Notes
- **Migration:** Add column with default value to avoid downtime.
- **ORM:** Update `User` model in SQLModel/SQLAlchemy.
