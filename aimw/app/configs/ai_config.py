from functools import lru_cache

from app.configs.base_config import BaseConfig, get_base_config


class AiConfig(BaseConfig):
    model_config = {"env_file": get_base_config().AI_CONFIG_FILE}


class AISettings(AiConfig):
    OPENAI_API_BASE: str = "https://api.openai.com/v1/"
    OPENAI_API_KEY: str = ""
    MODEL_NAME: str = "gpt-4.1"
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"


@lru_cache()
def get_ai_settings() -> AISettings:
    return AISettings()
