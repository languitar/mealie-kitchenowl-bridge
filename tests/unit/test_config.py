import pytest

from bridge.config import Config


def _set_required_env(monkeypatch):
    monkeypatch.setenv("OIDC_ISSUER", "http://idp.example")
    monkeypatch.setenv("OIDC_CLIENT_ID", "bridge-client")
    monkeypatch.setenv("OIDC_CLIENT_SECRET", "oidc-secret")
    monkeypatch.setenv("SECRET_KEY", "session-secret")
    monkeypatch.setenv("MEALIE_URL", "http://mealie.example")
    monkeypatch.setenv("MEALIE_API_TOKEN", "mealie-secret")


def test_from_env_reads_all_variables(monkeypatch):
    monkeypatch.setenv("KITCHENOWL_URL", "http://kitchenowl.example")
    monkeypatch.setenv("KITCHENOWL_API_TOKEN", "kitchenowl-secret")
    monkeypatch.setenv("KITCHENOWL_HOUSEHOLD_ID", "1")
    _set_required_env(monkeypatch)

    config = Config.from_env()

    assert config == Config(
        kitchenowl_url="http://kitchenowl.example",
        kitchenowl_api_token="kitchenowl-secret",
        kitchenowl_household_id="1",
        oidc_issuer="http://idp.example",
        oidc_client_id="bridge-client",
        oidc_client_secret="oidc-secret",
        secret_key="session-secret",
        mealie_url="http://mealie.example",
        mealie_api_token="mealie-secret",
    )


def test_from_env_defaults_to_empty_strings(monkeypatch):
    monkeypatch.delenv("KITCHENOWL_URL", raising=False)
    monkeypatch.delenv("KITCHENOWL_API_TOKEN", raising=False)
    monkeypatch.delenv("KITCHENOWL_HOUSEHOLD_ID", raising=False)
    _set_required_env(monkeypatch)

    config = Config.from_env()

    assert config == Config(
        kitchenowl_url="",
        kitchenowl_api_token="",
        kitchenowl_household_id="",
        oidc_issuer="http://idp.example",
        oidc_client_id="bridge-client",
        oidc_client_secret="oidc-secret",
        secret_key="session-secret",
        mealie_url="http://mealie.example",
        mealie_api_token="mealie-secret",
    )


def test_from_env_requires_oidc_issuer(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("OIDC_ISSUER", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_requires_oidc_client_id(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("OIDC_CLIENT_ID", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_requires_oidc_client_secret(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("OIDC_CLIENT_SECRET", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_requires_secret_key(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_requires_mealie_url(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("MEALIE_URL", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_requires_mealie_api_token(monkeypatch):
    _set_required_env(monkeypatch)
    monkeypatch.delenv("MEALIE_API_TOKEN", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()
