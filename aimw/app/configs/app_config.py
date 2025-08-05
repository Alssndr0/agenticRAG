from functools import lru_cache
from typing import Dict, List

from app.configs.base_config import BaseConfig, get_base_config
from pydantic import Field


class AppConfig(BaseConfig):
    model_config = {"env_file": get_base_config().APP_CONFIG_FILE}


class AppSettings(AppConfig):
    APP_NAME: str = "Traydstream"
    APP_VERSION: str = "v0.0.1"
    DESCRIPTION: str = "Traydstream Demo"
    CHECKS: Dict[str, str] = Field(
        default={
            # "swift": "../data/swift_message_fields.txt",
            # "ucp600": "../data/ucp_600.txt",
            "conflict": "../data/conflicting.txt",
        }
    )
    HOST: str = "127.0.0.1"
    AIMW_PORT: int = 8000
    API_VERSION: str = "/api/v1"
    API_KEYS: List[str] = Field(
        default_factory=list, description="List of allowed API keys"
    )


@lru_cache()
def get_app_settings() -> AppSettings:
    return AppSettings()
