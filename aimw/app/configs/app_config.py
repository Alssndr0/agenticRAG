from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Union

from app.configs.base_config import BaseConfig, get_base_config
from pydantic import Field


class Environment(str, Enum):
    PRODUCTION = "Production"
    STAGING = "Staging"
    QA = "QA"
    DEVELOPMENT = "Development"


class AppConfig(BaseConfig):
    model_config = {"env_file": get_base_config().APP_CONFIG_FILE}


class AppSettings(AppConfig):
    APP_NAME: str = Field(default="Lumera-SQ-RG-BE")
    APP_VERSION: str = Field(default="v0.0.1")
    API_VERSION: str = Field(default="/api/v1")
    API_KEYS: str = Field(default="nSx0eOtFUNw2QknCxEACgDJkjyO8z6xbTG6XnRhby4Q=")
    ENVIRONMENT: Environment = Field(default=Environment.DEVELOPMENT)
    ADMIN_EMAIL: str = Field(default="name.surname@lumera.com")
    AIMW_PORT: int = Field(default=7401, ge=1024, le=65535)
    HOST: str = Field(default="https://127.0.0.1")
    SERVERS: List[Dict[str, Union[str, Any]]] = []
    PROCESS_TIME_FORMAT: str = Field(default="{0:.8f}")


@lru_cache()
def get_app_settings() -> AppSettings:
    return AppSettings()
