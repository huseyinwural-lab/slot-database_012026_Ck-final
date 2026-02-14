import os
import pytest
import requests


def _api_base() -> str:
    # Prefer same env var used by frontend; fallback for local.
    return os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")


def _login_token() -> str:
    api = _api_base()
    r = requests.post(
        f"{api}/api/v1/auth/login",
        json={"email": os.environ.get("TEST_OWNER_EMAIL", "admin@casino.com"), "password": os.environ.get("TEST_OWNER_PASSWORD", "Admin123!")},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/crm/campaigns",
        "/api/v1/affiliates/",
    ],
)
def test_full_tenant_crm_aff_smoke(path: str):
    api = _api_base()
    token = _login_token()

    r = requests.get(
        f"{api}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": "default_casino",
        },
        timeout=30,
    )

    assert r.status_code == 200, r.text
