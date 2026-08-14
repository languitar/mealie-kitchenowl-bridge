import pytest

from bridge.config import Config


def test_from_env_reads_all_variables(monkeypatch):
    monkeypatch.setenv("KITCHENOWL_URL", "http://kitchenowl.example")
    monkeypatch.setenv("KITCHENOWL_API_TOKEN", "kitchenowl-secret")
    monkeypatch.setenv("KITCHENOWL_HOUSEHOLD_ID", "1")
    monkeypatch.setenv("TRIGGER_TOKEN", "trigger-secret")
    monkeypatch.setenv("MEALIE_URL", "http://mealie.example")
    monkeypatch.setenv("MEALIE_API_TOKEN", "mealie-secret")

    config = Config.from_env()

    assert config == Config(
        kitchenowl_url="http://kitchenowl.example",
        kitchenowl_api_token="kitchenowl-secret",
        kitchenowl_household_id="1",
        trigger_token="trigger-secret",
        mealie_url="http://mealie.example",
        mealie_api_token="mealie-secret",
    )


def test_from_env_defaults_to_empty_strings(monkeypatch):
    monkeypatch.delenv("KITCHENOWL_URL", raising=False)
    monkeypatch.delenv("KITCHENOWL_API_TOKEN", raising=False)
    monkeypatch.delenv("KITCHENOWL_HOUSEHOLD_ID", raising=False)
    monkeypatch.setenv("TRIGGER_TOKEN", "trigger-secret")
    monkeypatch.setenv("MEALIE_URL", "http://mealie.example")
    monkeypatch.setenv("MEALIE_API_TOKEN", "mealie-secret")

    config = Config.from_env()

    assert config == Config(
        kitchenowl_url="",
        kitchenowl_api_token="",
        kitchenowl_household_id="",
        trigger_token="trigger-secret",
        mealie_url="http://mealie.example",
        mealie_api_token="mealie-secret",
    )


def test_from_env_requires_trigger_token(monkeypatch):
    monkeypatch.delenv("TRIGGER_TOKEN", raising=False)
    monkeypatch.setenv("MEALIE_URL", "http://mealie.example")
    monkeypatch.setenv("MEALIE_API_TOKEN", "mealie-secret")

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_requires_mealie_url(monkeypatch):
    monkeypatch.setenv("TRIGGER_TOKEN", "trigger-secret")
    monkeypatch.delenv("MEALIE_URL", raising=False)
    monkeypatch.setenv("MEALIE_API_TOKEN", "mealie-secret")

    with pytest.raises(RuntimeError):
        Config.from_env()


def test_from_env_requires_mealie_api_token(monkeypatch):
    monkeypatch.setenv("TRIGGER_TOKEN", "trigger-secret")
    monkeypatch.setenv("MEALIE_URL", "http://mealie.example")
    monkeypatch.delenv("MEALIE_API_TOKEN", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()
