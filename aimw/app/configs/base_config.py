import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONF_DIR = Path(os.getenv("CONF_DIR", default=BASE_DIR / "conf"))


class BaseConfig(BaseSettings):
    """Base configuration class providing a shared default model
    configuration."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file_encoding="utf-8",
        env_file=str(CONF_DIR / "base_config.env"),
        extra="ignore",
    )

    AI_CONFIG_FILE: Path = Field(default=CONF_DIR / "ai_config.env")
    APP_CONFIG_FILE: Path = Field(default=CONF_DIR / "app_config.env")
    LOGS_CONFIG_FILE: Path = Field(default=CONF_DIR / "logs_config.env")


@lru_cache()
def get_base_config() -> BaseConfig:
    return BaseConfig()
