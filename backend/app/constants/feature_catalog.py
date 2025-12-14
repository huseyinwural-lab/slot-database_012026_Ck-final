from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal


Visibility = Literal["owner_only", "tenant"]


@dataclass(frozen=True)
class FeatureModule:
    module_key: str
    label: str
    route_prefix: str
    required_flag: str
    visibility: Visibility
    non_core: bool = True


# Canonical catalog (single source of truth)
FEATURE_CATALOG: Dict[str, FeatureModule] = {
    "experiments": FeatureModule(
        module_key="experiments",
        label="Feature Flags & A/B Testing",
        route_prefix="/features",
        required_flag="can_manage_experiments",
        visibility="owner_only",
        non_core=True,
    ),
    "kill_switch": FeatureModule(
        module_key="kill_switch",
        label="Kill Switch",
        route_prefix="/kill-switch",
        required_flag="can_use_kill_switch",
        visibility="owner_only",
        non_core=True,
    ),
    "affiliates": FeatureModule(
        module_key="affiliates",
        label="Affiliate Program",
        route_prefix="/affiliates",
        required_flag="can_manage_affiliates",
        visibility="tenant",
        non_core=True,
    ),
    "crm": FeatureModule(
        module_key="crm",
        label="CRM & Communications",
        route_prefix="/crm",
        required_flag="can_use_crm",
        visibility="tenant",
        non_core=True,
    ),
}


def list_modules() -> List[FeatureModule]:
    return list(FEATURE_CATALOG.values())
