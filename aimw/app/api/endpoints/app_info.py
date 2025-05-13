import fastapi
from app.configs.app_config import AppSettings, get_app_settings
from fastapi import APIRouter, Depends
from loguru import logger

router = APIRouter()


@router.get(
    path="/api_info",
    response_model=AppSettings,
    status_code=fastapi.status.HTTP_200_OK,
)
async def fetch_info(settings: AppSettings = Depends(get_app_settings)):
    """
    Provides basic App Info.
    """
    logger.info("Logger levels:")
    logger.trace("TRACE: 5")
    logger.debug("DEBUG: 10")
    logger.info("INFO: 20")
    logger.success("SUCCESS: 25")
    logger.warning("WARNING: 30")
    logger.error("ERROR: 40")
    logger.critical("CRITICAL: 50")
    return settings


@router.get("/.well-known/live", status_code=fastapi.status.HTTP_200_OK)
def live():
    """Liveness checks endpoint

    Returns:
        status: "OK"
    """
    return {"message": "OK"}
