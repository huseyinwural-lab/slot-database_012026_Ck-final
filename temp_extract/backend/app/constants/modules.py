"""Canonical tenant feature flags (module-level permissions).

These flags live under Tenant.features and are used by backend enforcement
(ensure_tenant_feature) and, optionally, by the frontend for gating menus.
"""

MODULE_FEATURE_FLAGS = {
    # Game configuration editing (all math/advanced/general config endpoints)
    "can_edit_configs": "Allows editing game configurations (RTP, math, advanced settings)",
    # Bonus configuration and campaigns
    "can_manage_bonus": "Allows configuring and managing bonus campaigns and bonus settings",
    # Reporting / analytics screens
    "can_view_reports": "Allows access to reporting/analytics modules",
    # Game Robot (test automation / load)
    "can_use_game_robot": "Allows using the Game Robot / orchestrator endpoints",
    # Finance/transactions modules (optional, not fully wired yet)
    "can_manage_finance": "Allows access to finance/transaction management modules",
    # Admin/API key/tenant level management (optional, minimal usage)
    "can_manage_admins": "Allows managing admin-level resources such as API keys and tenant-level settings",
}
