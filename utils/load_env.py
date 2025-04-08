import os

from dotenv import load_dotenv


def load_env_vars():
    """Load environment variables from .env file and return a dict of common settings."""
    load_dotenv()

    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "OPENAI_API_URL": os.getenv(
            "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
        ),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "OPENAI_MAX_TOKENS": int(os.getenv("OPENAI_MAX_TOKENS", "1200")),
        "VLM_PROMPT": os.getenv("VLM_PROMPT", ""),
    }


# Singleton-like pattern - load once when module is imported
ENV_VARS = load_env_vars()


def get_env_vars():
    """Get the loaded environment variables."""
    return ENV_VARS
