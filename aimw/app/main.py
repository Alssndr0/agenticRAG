import gc
import platform
import random
import string
import time
from contextlib import asynccontextmanager
from typing import Any

import psutil
from app import state
from app.api.routes import api_router
from app.configs.ai_config import get_ai_settings
from app.configs.app_config import get_app_settings
from app.configs.log_config import LoggingSettings, setup_app_logging
from app.loaders.base_loader import BaseModelLoader
from app.loaders.load_embeddings import BgeEmbeddingsLoader
from app.services.retrieve import HybridRetriever
from app.services.security import api_key_auth
from app.utils.minio_utils.minio_client import MinioClient
from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from huggingface_hub import InferenceClient
from loguru import logger

# Setup logging as early as possible.
setup_app_logging(config=LoggingSettings())

# Ensure the embeddings model is available before loading.
MinioClient().ensure_model_available()
# Ensure the BM25 index is available before loading.
MinioClient().ensure_bm25index_available()
# Ensure the FAISS index is available before loading.
MinioClient().ensure_faissindex_available()

# Expose the shared registry as a module-level variable.
ai_models = BaseModelLoader.ai_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Log CPU information.
    cpu_info = (
        f"CPU Information: | "
        f"Physical Cores: {psutil.cpu_count(logical=False)} | "
        f"Total Cores: {psutil.cpu_count(logical=True)} | "
        f"Architecture: {platform.machine()} | "
        f"Processor: {platform.processor()}"
    )
    logger.info(cpu_info)

    # Directly load the embeddings model using BgeEmbeddingsLoader.
    embedding_model_id = get_ai_settings().EMBEDDING_MODEL
    ai_models[embedding_model_id] = BgeEmbeddingsLoader().load()
    logger.info("Embedding model initialized and stored in app state.")
    logger.info(ai_models[embedding_model_id])

    # Initialize the InferenceClient and store it in app state.
    url = get_ai_settings().LLM_ENDPOINT
    app.state.inference_client = InferenceClient(model=url)
    state.set_inference_client(app.state.inference_client)
    logger.info("InferenceClient initialized and stored in app state.")

    # Initialize the HybridRetriever with the pre-loaded embeddings model.
    # (Import here to avoid circular imports.)
    app.state.retriever = HybridRetriever(
        model_embeddings=ai_models[embedding_model_id]
    )
    state.set_retriever(app.state.retriever)
    logger.info("HybridRetriever initialized and stored in app state.")

    yield

    # On shutdown, clear the loaded AI models and free resources.
    ai_models.clear()
    gc.collect()


root_router = APIRouter()


@root_router.get(path="/", status_code=200)
async def root():
    """Root GET Endpoint"""
    return {"message": "Demo - Agentic GraphRAG"}


app = FastAPI(
    title=get_app_settings().APP_NAME,
    description="APIs to expose Agentic GraphRAG as a service.",
    version=get_app_settings().APP_VERSION,
    servers=get_app_settings().SERVERS,
    lifespan=lifespan,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next) -> Any:
    """
    Middleware to measure processing time and add it to the response header.
    """
    # Generate a unique ID for the request
    request_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={request_id} start request path={request.url.path}")

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    formatted_process_time = get_app_settings().PROCESS_TIME_FORMAT.format(process_time)
    response.headers["X-Process-Time"] = f"{formatted_process_time} sec"

    logger.info(
        f"rid={request_id} completed_in={formatted_process_time} sec status_code={response.status_code}"
    )
    return response


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
    import uvicorn

    uvicorn.run(
        app,
        host=get_app_settings().HOST,
        port=get_app_settings().AIMW_PORT,
        log_level="debug",
    )
