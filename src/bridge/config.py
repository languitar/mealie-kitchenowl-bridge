import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    kitchenowl_url: str
    kitchenowl_api_token: str
    kitchenowl_household_id: str
    trigger_token: str
    mealie_url: str
    mealie_api_token: str

    @classmethod
    def from_env(cls) -> Config:
        trigger_token = os.environ.get("TRIGGER_TOKEN", "")
        if not trigger_token:
            raise RuntimeError(
                "TRIGGER_TOKEN must be set - refusing to start without a trigger secret."
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
            trigger_token=trigger_token,
            mealie_url=mealie_url,
            mealie_api_token=mealie_api_token,
        )
