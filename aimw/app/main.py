import uvicorn
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import api_router
from app.configs.app_config import get_app_settings
from app.configs.log_config import LoggingSettings, setup_app_logging
from app.services.security import api_key_auth

# Setup logging as early as possible.
setup_app_logging(config=LoggingSettings())

root_router = APIRouter()


@root_router.get(path="/", status_code=200)
async def root():
    """Root GET Endpoint"""
    return {"message": "Traydstream Demo"}


app = FastAPI(
    title=get_app_settings().APP_NAME,
    description=get_app_settings().DESCRIPTION,
    version=get_app_settings().APP_VERSION,
)

# Include API routes (with API key authentication)
app.include_router(
    api_router,
    prefix=get_app_settings().API_VERSION,
    dependencies=[Depends(api_key_auth)],
)
app.include_router(root_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run the app (for debugging/development only)
if __name__ == "__main__":
    logger.warning("Running in development mode. Do not run in production.")
    uvicorn.run(
        app,
        host=get_app_settings().HOST,
        port=get_app_settings().AIMW_PORT,
        log_level="debug",
    )
