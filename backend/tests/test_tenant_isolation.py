import os
import pytest
import requests


def _api_base() -> str:
    return os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")


def _login(email: str, password: str) -> str:
    api = _api_base()
    r = requests.post(
        f"{api}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _create_tenant_admin(owner_token: str, email: str, tenant_id: str):
    api = _api_base()
    r = requests.post(
        f"{api}/api/v1/admin/create-tenant-admin",
        json={"email": email, "tenant_id": tenant_id, "password": "TenantAdmin123!", "full_name": "Tenant Admin"},
        headers={"Authorization": f"Bearer {owner_token}"},
        timeout=30,
    )
    # If already exists, backend returns 400 ADMIN_EXISTS; accept it.
    if r.status_code not in (200, 400):
        raise AssertionError(r.text)


def test_tenant_admin_header_forbidden_403():
    api = _api_base()

    owner_token = _login("admin@casino.com", "Admin123!")
    tenant_admin_email = "tenant.admin@demo-renter.com"
    _create_tenant_admin(owner_token, tenant_admin_email, "demo_renter")

    tenant_token = _login(tenant_admin_email, "TenantAdmin123!")

    r = requests.get(
        f"{api}/api/v1/api-keys/",
        headers={
            "Authorization": f"Bearer {tenant_token}",
            "X-Tenant-ID": "default_casino",
        },
        timeout=30,
    )

    assert r.status_code == 403, r.text
    detail = r.json().get("detail")
    assert isinstance(detail, dict)
    assert detail.get("error_code") == "TENANT_HEADER_FORBIDDEN"


def test_owner_invalid_header_400():
    api = _api_base()
    owner_token = _login("admin@casino.com", "Admin123!")

    r = requests.get(
        f"{api}/api/v1/api-keys/",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "X-Tenant-ID": "__does_not_exist__",
        },
        timeout=30,
    )

    assert r.status_code == 400, r.text
    detail = r.json().get("detail")
    assert isinstance(detail, dict)
    assert detail.get("error_code") == "INVALID_TENANT_HEADER"


def test_owner_headerless_default_scope_200():
    api = _api_base()
    owner_token = _login("admin@casino.com", "Admin123!")

    r = requests.get(
        f"{api}/api/v1/api-keys/",
        headers={"Authorization": f"Bearer {owner_token}"},
        timeout=30,
    )

    assert r.status_code == 200, r.text


def test_cross_tenant_detail_access_404():
    api = _api_base()

    owner_token = _login("admin@casino.com", "Admin123!")
    tenant_admin_email = "tenant.admin@demo-renter.com"
    _create_tenant_admin(owner_token, tenant_admin_email, "demo_renter")

    # Create a player in default_casino by registering via player auth
    r_reg = requests.post(
        f"{api}/api/v1/auth/player/register",
        json={"email": "isolation_test_player@casino.com", "username": "iso_player", "tenant_id": "default_casino", "password": "Player123!"},
        timeout=30,
    )
    # Either created or already exists
    assert r_reg.status_code in (200, 400), r_reg.text
    player_id = r_reg.json().get("player_id") if r_reg.status_code == 200 else None

    # If player already exists, fetch players as owner to get one id from default_casino
    if not player_id:
        r_list = requests.get(
            f"{api}/api/v1/players?page=1&page_size=5&include_total=true",
            headers={"Authorization": f"Bearer {owner_token}"},
            timeout=30,
        )
        assert r_list.status_code == 200, r_list.text
        items = r_list.json().get("items") or []
        assert items, "Expected at least one player in default_casino"
        player_id = items[0]["id"]

    # Login as tenant admin for demo_renter and try to access that player by id
    tenant_token = _login(tenant_admin_email, "TenantAdmin123!")

    r = requests.get(
        f"{api}/api/v1/players/{player_id}",
        headers={"Authorization": f"Bearer {tenant_token}"},
        timeout=30,
    )
    assert r.status_code == 404, r.text


def test_owner_impersonation_works_for_other_tenant_200():
    api = _api_base()
    owner_token = _login("admin@casino.com", "Admin123!")

    # Owner impersonate demo_renter capabilities (should work if tenant exists)
    r = requests.get(
        f"{api}/api/v1/tenants/capabilities",
        headers={"Authorization": f"Bearer {owner_token}", "X-Tenant-ID": "demo_renter"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("tenant_id") == "demo_renter"
