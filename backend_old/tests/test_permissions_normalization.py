from app.services.rbac import ROLE_ADMIN, ROLE_OPS, ROLE_SUPPORT
from app.utils.permissions import require_admin, require_ops, require_support_view


class Dummy:
    def __init__(self, role: str, is_platform_owner: bool = False):
        self.role = role
        self.is_platform_owner = is_platform_owner


def test_permissions_accept_tenant_admin_as_admin_and_ops_and_support_view():
    admin = Dummy("Tenant Admin")
    # Should not raise
    require_admin(admin)
    require_ops(admin)
    require_support_view(admin)


def test_permissions_accept_ops_aliases():
    ops = Dummy("Operations")
    require_ops(ops)


def test_permissions_support_view_aliases():
    support = Dummy("CS")
    require_support_view(support)
