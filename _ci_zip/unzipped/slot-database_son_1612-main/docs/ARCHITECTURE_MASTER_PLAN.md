# Architecture Master Plan & Contract

This document serves as the "Source of Truth" for the Tenant/Admin Architecture.

## 0) Preparation & Contracts

### Tenant / Admin / Role / Permission Contract
*   **Tenant Identity:** Passed via `X-Tenant-ID` header.
*   **Admin Context:** Resolved via JWT `sub` -> `AdminUser` -> `tenant_id` + `tenant_role`.
*   **Feature Flags:** Backend uses `ensure_tenant_feature(flag)`. Frontend uses `RequireFeature` HOC.

### API Contract & Error Standards
All API errors must follow this JSON format:
```json
{
  "error_code": "RESOURCE_NOT_FOUND",
  "message": "The requested player was not found.",
  "details": { "id": "123" },
  "timestamp": "2023-10-27T10:00:00Z"
}
```
*   **401:** Unauthorized (Invalid/Missing Token)
*   **403:** Forbidden (Valid Token, Insufficient Permissions/Role)
*   **404:** Resource Not Found (Tenant scoped)
*   **422:** Validation Error (Pydantic standard)

## 1) Onboarding & Identity

*   **Login:** JWT based (Access + Refresh strategy).
*   **Invite Flow:** Admin Create -> Invite Token -> Email Link -> Set Password -> Active.
*   **Security:** Rate limiting on login endpoints.

## 2) Context & RBAC

*   **Tenant Resolver:** Backend dependency `get_current_tenant_id`.
*   **RBAC:** `require_tenant_role(["finance", "operations"])`.
*   **Audit:** All write actions must log to `AdminActivityLog`.

## 3) App Skeleton (Tenant UI)

*   **Global State:** `CapabilitiesContext` holds `tenant_role` and `features`.
*   **Layout:** Sidebar visibility controlled by `isOwner` and `features`.

## 4) Tenant Modules (Implemented)

*   4.1 Dashboard
*   4.2 Players (List, Detail, KYC, Balance)
*   4.3 Games (Catalog, Config, RTP)
*   4.4 Bonuses (Rules, Trigger)
*   4.5 Reports (Revenue)
*   4.6 Finance (Transactions, Payout Approval)

## 5) Tenant Admin Management

*   Create/Invite Sub-admins.
*   Role Assignment (Finance, Ops, Support).
*   Permission Matrix (Read-only view for now).

## 6) API Keys & Integrations

*   API Key CRUD with scopes.
*   IP Allowlist per key.

## 7) Settings & Security

*   Tenant Settings (Brand, Locale).
*   Security Hardening (Session timeout).

## 8) Observability

*   Structured Logging.
*   Health Checks.

## 9) Release & Ops

*   Seeding Scripts.
*   Migration strategy.
