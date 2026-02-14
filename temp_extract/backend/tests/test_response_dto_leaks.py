import os
import pytest
import requests


SENSITIVE_KEYS = {
    "password_hash",
    "invite_token",
    "password_reset_token",
    "key_hash",
    # generic
    "secret",
    "jwt",
    "token",
}


def _api_base() -> str:
    return os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")


def _login_token() -> str:
    api = _api_base()
    email = os.environ.get("TEST_OWNER_EMAIL", "admin@casino.com")
    password = os.environ.get("TEST_OWNER_PASSWORD", "Admin123!")

    r = requests.post(
        f"{api}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _assert_no_sensitive(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in SENSITIVE_KEYS, f"Sensitive key leaked: {k}"
            _assert_no_sensitive(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_sensitive(item)


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/players"),
        ("GET", "/api/v1/api-keys/"),
    ],
)
def test_no_sensitive_fields_in_responses(method: str, path: str):
    api = _api_base()
    token = _login_token()

    r = requests.request(
        method,
        f"{api}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    _assert_no_sensitive(body)


def test_api_key_create_returns_secret_once_but_not_in_list():
    api = _api_base()
    token = _login_token()

    # Create should return api_key once
    r = requests.post(
        f"{api}/api/v1/api-keys/",
        json={"name": "Leak Test", "scopes": ["robot.run"]},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert "api_key" in body and isinstance(body["api_key"], str) and len(body["api_key"]) > 10
    assert "key" in body and isinstance(body["key"], dict)

    # secret must not appear inside key meta
    assert "key_hash" not in body["key"]

    # List must not include api_key nor key_hash
    r2 = requests.get(
        f"{api}/api/v1/api-keys/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert r2.status_code == 200, r2.text
    items = r2.json()
    _assert_no_sensitive(items)
    # also ensure the create-only field isn't present
    assert all("api_key" not in item for item in items)
