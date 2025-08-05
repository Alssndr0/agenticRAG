from app.api.endpoints import app_info, run_check
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(app_info.router, prefix="/info", tags=["info"])
api_router.include_router(run_check.router, prefix="/run", tags=["run-check"])
