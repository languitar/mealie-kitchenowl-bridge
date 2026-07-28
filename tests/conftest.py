import pytest

from bridge.app import create_app
from bridge.config import Config


@pytest.fixture
def config() -> Config:
    return Config(
        kitchenowl_url="http://kitchenowl.test",
        kitchenowl_api_token="kitchenowl-token",
        kitchenowl_household_id="1",
        webhook_token="webhook-token",
    )


@pytest.fixture
def app(config: Config):
    return create_app(config)
