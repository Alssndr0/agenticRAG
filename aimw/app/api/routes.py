from app.api.endpoints import app_info, generate
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(app_info.router, prefix="/info", tags=["info"])
api_router.include_router(generate.router, prefix="/rg", tags=["Retriever"])
