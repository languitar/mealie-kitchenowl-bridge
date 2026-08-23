import pytest

from bridge.app import create_app
from bridge.config import Config


@pytest.fixture
def config() -> Config:
    return Config(
        kitchenowl_url="http://kitchenowl.test",
        kitchenowl_api_token="kitchenowl-token",
        kitchenowl_household_id="1",
        oidc_issuer="http://idp.test",
        oidc_client_id="bridge-client",
        oidc_client_secret="oidc-client-secret",
        secret_key="test-secret-key",
        mealie_url="http://mealie.test",
        mealie_api_token="mealie-token",
    )


@pytest.fixture
def app(config: Config):
    return create_app(config)
