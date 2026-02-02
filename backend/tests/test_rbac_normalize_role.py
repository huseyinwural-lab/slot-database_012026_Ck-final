from app.services.rbac import normalize_role, ROLE_ADMIN, ROLE_OPS, ROLE_SUPPORT, ROLE_SUPER_ADMIN


def test_normalize_role_aliases():
    # Tenant Admin -> ADMIN
    assert normalize_role("Tenant Admin") == ROLE_ADMIN
    assert normalize_role("TENANT_ADMIN") == ROLE_ADMIN
    assert normalize_role("tenant_admin") == ROLE_ADMIN
    assert normalize_role("ADMIN") == ROLE_ADMIN

    # Ops -> OPS
    assert normalize_role("Ops") == ROLE_OPS
    assert normalize_role("OPS") == ROLE_OPS
    assert normalize_role("Operations") == ROLE_OPS

    # Support -> SUPPORT
    assert normalize_role("Support") == ROLE_SUPPORT
    assert normalize_role("SUPPORT") == ROLE_SUPPORT
    assert normalize_role("CS") == ROLE_SUPPORT

    # Super admin
    assert normalize_role("Super Admin") == ROLE_SUPER_ADMIN
    assert normalize_role("SUPERADMIN") == ROLE_SUPER_ADMIN
