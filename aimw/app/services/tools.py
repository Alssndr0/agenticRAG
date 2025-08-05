from app.configs.app_config import get_app_settings
from app.schemas.agent_schemas import AgentState
from loguru import logger

APP_CONFIG = get_app_settings()
CHECKS = APP_CONFIG.CHECKS


def retrieve_document(document_path: str) -> str:
    """
    Retrieve a document from a given path.

    Args:
        document_path (str): The path to the document.

    Returns:
        str: The content of the document.
    """
    try:
        with open(document_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(
            f"Warning: File {document_path} not found. Using placeholder content."
        )
        return f"[Placeholder content for {document_path}]"
    except Exception as e:
        logger.error(f"Error reading {document_path}: {e}")
        return f"[Error reading {document_path}]"


def prepare_document(state: AgentState) -> dict:
    """Initialize the checking process by setting up pending checks."""
    logger.info("Preparing document for compliance checks...")
    return {
        "pending_checks": list(CHECKS.keys()),
        "current_check": "",
        "check_results": [],
    }
