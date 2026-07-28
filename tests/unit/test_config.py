import pytest

from bridge.config import Config


def test_from_env_reads_all_variables(monkeypatch):
    monkeypatch.setenv("KITCHENOWL_URL", "http://kitchenowl.example")
    monkeypatch.setenv("KITCHENOWL_API_TOKEN", "kitchenowl-secret")
    monkeypatch.setenv("KITCHENOWL_HOUSEHOLD_ID", "1")
    monkeypatch.setenv("WEBHOOK_TOKEN", "webhook-secret")

    config = Config.from_env()

    assert config == Config(
        kitchenowl_url="http://kitchenowl.example",
        kitchenowl_api_token="kitchenowl-secret",
        kitchenowl_household_id="1",
        webhook_token="webhook-secret",
    )


def test_from_env_defaults_to_empty_strings(monkeypatch):
    monkeypatch.delenv("KITCHENOWL_URL", raising=False)
    monkeypatch.delenv("KITCHENOWL_API_TOKEN", raising=False)
    monkeypatch.delenv("KITCHENOWL_HOUSEHOLD_ID", raising=False)
    monkeypatch.setenv("WEBHOOK_TOKEN", "webhook-secret")

    config = Config.from_env()

    assert config == Config(
        kitchenowl_url="",
        kitchenowl_api_token="",
        kitchenowl_household_id="",
        webhook_token="webhook-secret",
    )


def test_from_env_requires_webhook_token(monkeypatch):
    monkeypatch.delenv("WEBHOOK_TOKEN", raising=False)

    with pytest.raises(RuntimeError):
        Config.from_env()
