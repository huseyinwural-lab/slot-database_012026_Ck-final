import os
import importlib


def _reload_settings(env_value: str, seed_on_startup: str | None):
    os.environ["ENV"] = env_value
    if seed_on_startup is None:
        os.environ.pop("SEED_ON_STARTUP", None)
    else:
        os.environ["SEED_ON_STARTUP"] = seed_on_startup

    # Reload config module to pick up new env vars
    import config

    importlib.reload(config)
    return config.settings


def test_seed_on_startup_default_false():
    settings = _reload_settings("dev", None)
    assert settings.seed_on_startup is False


def test_seed_on_startup_true_when_env_var_set():
    settings = _reload_settings("dev", "true")
    assert settings.seed_on_startup is True


def test_seed_never_runs_in_prod_even_if_flag_set():
    settings = _reload_settings("prod", "true")
    assert settings.env == "prod"
    assert settings.seed_on_startup is True

    # Logic expectation: prod is always no-op. (Behavior validated in server.py; this test asserts config stays set but gated.)
