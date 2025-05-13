from functools import lru_cache
from pathlib import Path

from app.configs.base_config import BASE_DIR, BaseConfig, get_base_config


class MinioConfig(BaseConfig):
    model_config = {"env_file": get_base_config().MINIO_CONFIG_FILE}


class MinioSettings(MinioConfig):
    """MinIO Settings as a class holder for MinIO config."""

    ENDPOINT: str = "objects.ai-staging.com:9000"
    ACCESS_KEY: str = "mEIG785V6l83X20KjRlS"
    SECRET_KEY: str = "V5A4ERTUPHqHYMJ40KEb3y1rTClhK3vJwY7CeUnl"
    BUCKET: str = "experiment"
    MODEL: str = "bge-large-en-v1.5"
    MODEL_VERSION: str = "v0.0.1"

    # embedding model details
    MINIO_MODEL_DIR: str = "AI-LLA-SQA/ai-models/"  # NOTE: the embedding model must be the same used to create the KB!
    MINIO_MODEL_PATH: str = MINIO_MODEL_DIR + MODEL_VERSION + MODEL
    LOCAL_MODEL_DIR: Path = BASE_DIR / "resources" / "ai-models"
    LOCAL_MODEL_PATH: Path = LOCAL_MODEL_DIR / MODEL_VERSION / MODEL

    # BM25 index details
    BM25_INDEX_TIMESTAMP: str = "20250226_181824"
    MINIO_BM25_DIR: str = "AI-LLA-SQA/kb_indexes/bm25/"
    MINIO_BM25_DIR: str = MINIO_BM25_DIR + BM25_INDEX_TIMESTAMP
    LOCAL_BM25_DIR: Path = BASE_DIR / "indexes" / "bm25"
    LOCAL_BM25_PATH: Path = LOCAL_BM25_DIR / BM25_INDEX_TIMESTAMP / "bm25.pkl"

    # FAISS index details (fixed incorrect timestamp usage)
    FAISS_INDEX_TIMESTAMP: str = "20250226_181952"
    MINIO_FAISS_DIR: str = "AI-LLA-SQA/kb_indexes/faiss/"
    MINIO_FAISS_DIR: str = MINIO_FAISS_DIR + FAISS_INDEX_TIMESTAMP
    LOCAL_FAISS_DIR: Path = BASE_DIR / "indexes" / "faiss"
    LOCAL_FAISS_PATH: Path = LOCAL_FAISS_DIR / FAISS_INDEX_TIMESTAMP


@lru_cache()
def get_minio_settings() -> MinioSettings:
    return MinioSettings()
