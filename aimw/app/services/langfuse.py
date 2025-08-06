from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from loguru import logger

from app.configs.ai_config import get_ai_settings

# Initialize Langfuse client with settings from configuration
AI_CONFIG = get_ai_settings()

langfuse = Langfuse(
    public_key=AI_CONFIG.LANGFUSE_PUBLIC_KEY,
    secret_key=AI_CONFIG.LANGFUSE_SECRET_KEY,
    host=AI_CONFIG.LANGFUSE_HOST,
)

# Verify connection
if langfuse.auth_check():
    logger.info("Langfuse client is authenticated and ready!")
else:
    logger.info("Authentication failed. Please check your credentials and host.")

langfuse_handler = CallbackHandler()
