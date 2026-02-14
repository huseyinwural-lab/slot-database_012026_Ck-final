import pathlib
import pytest


def test_bootstrap_owner_script_is_present_and_safe():
    p = pathlib.Path('/app/backend/scripts/bootstrap_owner.py')
    assert p.exists()

    txt = p.read_text()
    # Must be env gated
    assert 'BOOTSTRAP_OWNER_EMAIL' in txt
    assert 'BOOTSTRAP_OWNER_PASSWORD' in txt


@pytest.mark.parametrize("env_value", ["prod", "staging"]) 
def test_start_prod_calls_bootstrap(env_value: str):
    p = pathlib.Path('/app/backend/scripts/start_prod.sh')
    txt = p.read_text()
    assert 'alembic upgrade head' in txt
    assert 'bootstrap_owner.py' in txt
    assert 'BOOTSTRAP_OWNER_EMAIL' in (pathlib.Path('/app/backend/scripts/bootstrap_owner.py').read_text())
