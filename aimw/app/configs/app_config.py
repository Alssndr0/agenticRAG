from functools import lru_cache
from typing import Dict

from app.configs.base_config import BaseConfig, get_base_config
from pydantic import Field


class AppConfig(BaseConfig):
    model_config = {"env_file": get_base_config().APP_CONFIG_FILE}


class AppSettings(AppConfig):
    APP_NAME: str = Field(default="Traydstream")
    APP_VERSION: str = Field(default="v0.0.1")
    API_VERSION: str = Field(default="/api/v1")
    CHECKS: Dict[str, str] = Field(
        default={
            "swift": "../data/swift_message_fields.txt",
            "ucp600": "../data/ucp_600.txt",
            "conflict": "../data/conflicting.txt",
        }
    )


@lru_cache()
def get_app_settings() -> AppSettings:
    return AppSettings()
