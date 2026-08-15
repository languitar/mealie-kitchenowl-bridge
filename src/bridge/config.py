import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    kitchenowl_url: str
    kitchenowl_api_token: str
    kitchenowl_household_id: str
    oidc_issuer: str
    oidc_client_id: str
    oidc_client_secret: str
    secret_key: str
    mealie_url: str
    mealie_api_token: str

    @classmethod
    def from_env(cls) -> Config:
        oidc_issuer = os.environ.get("OIDC_ISSUER", "")
        if not oidc_issuer:
            raise RuntimeError(
                "OIDC_ISSUER must be set - refusing to start without an identity provider."
            )
        oidc_client_id = os.environ.get("OIDC_CLIENT_ID", "")
        if not oidc_client_id:
            raise RuntimeError(
                "OIDC_CLIENT_ID must be set - refusing to start without an identity provider."
            )
        oidc_client_secret = os.environ.get("OIDC_CLIENT_SECRET", "")
        if not oidc_client_secret:
            raise RuntimeError(
                "OIDC_CLIENT_SECRET must be set - refusing to start without an identity provider."
            )
        secret_key = os.environ.get("SECRET_KEY", "")
        if not secret_key:
            raise RuntimeError(
                "SECRET_KEY must be set - refusing to start without a session-signing secret."
            )
        mealie_url = os.environ.get("MEALIE_URL", "")
        if not mealie_url:
            raise RuntimeError(
                "MEALIE_URL must be set - refusing to start without a way to fetch recipes."
            )
        mealie_api_token = os.environ.get("MEALIE_API_TOKEN", "")
        if not mealie_api_token:
            raise RuntimeError(
                "MEALIE_API_TOKEN must be set - refusing to start without a way to fetch recipes."
            )
        return cls(
            kitchenowl_url=os.environ.get("KITCHENOWL_URL", ""),
            kitchenowl_api_token=os.environ.get("KITCHENOWL_API_TOKEN", ""),
            kitchenowl_household_id=os.environ.get("KITCHENOWL_HOUSEHOLD_ID", ""),
            oidc_issuer=oidc_issuer,
            oidc_client_id=oidc_client_id,
            oidc_client_secret=oidc_client_secret,
            secret_key=secret_key,
            mealie_url=mealie_url,
            mealie_api_token=mealie_api_token,
        )
