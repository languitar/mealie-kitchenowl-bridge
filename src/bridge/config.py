import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    mealie_url: str
    mealie_api_token: str
    kitchenowl_url: str
    kitchenowl_api_token: str
    kitchenowl_household_id: str
    webhook_token: str

    @classmethod
    def from_env(cls) -> Config:
        webhook_token = os.environ.get("WEBHOOK_TOKEN", "")
        if not webhook_token:
            raise RuntimeError(
                "WEBHOOK_TOKEN must be set - refusing to start without a webhook secret."
            )
        return cls(
            mealie_url=os.environ.get("MEALIE_URL", ""),
            mealie_api_token=os.environ.get("MEALIE_API_TOKEN", ""),
            kitchenowl_url=os.environ.get("KITCHENOWL_URL", ""),
            kitchenowl_api_token=os.environ.get("KITCHENOWL_API_TOKEN", ""),
            kitchenowl_household_id=os.environ.get("KITCHENOWL_HOUSEHOLD_ID", ""),
            webhook_token=webhook_token,
        )
