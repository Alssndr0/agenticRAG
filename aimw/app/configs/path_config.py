from functools import lru_cache
from pathlib import Path

from app.configs.base_config import BASE_DIR, BaseConfig, get_base_config
from app.configs.minio_config import get_minio_settings
from pydantic import Field


class PathConfig(BaseConfig):
    model_config = {"env_file": get_base_config().PATH_CONFIG_FILE}


class PathSettings(PathConfig):
    """
    Defines the configuration settings for file paths used in the application.
    Attributes:
        INPUT_PATH (Path): The directory path for input resources.
    """

    # FAISS_INDEX_PATH=indexes/FAISS-TEST/enhanced_chunks_20250412_193515
    # BM25_INDEX_PATH=indexes/bm25/bm25_index_20250412_193515.pkl
    FAISS_DIR: Path = Field(default=BASE_DIR / "indexes" / "faiss")
    FAISS_INDEX: Path = get_minio_settings().LOCAL_FAISS_PATH
    BM25_DIR: Path = Field(default=BASE_DIR / "indexes" / "bm25")
    BM25_INDEX: Path = get_minio_settings().LOCAL_BM25_PATH
    GRAPH_INDEX_PATH: Path = (
        Field(default=BASE_DIR / "data" / "indexes" / "graph_index"),
    )
    UPLOAD_DIR: Path = Field(default=BASE_DIR / "resources" / "uploads")
    OUTPUT_DIR: Path = Field(default=BASE_DIR / "resources" / "outputs")
    SUMMARISE_OUTPUT_FILE: Path = BASE_DIR / "data" / "enhanced" / "doc_summaries.json"
    SUMMARISE_CHUNK_OUTPUT_FILE: Path = (
        BASE_DIR / "data" / "enhanced" / "chunk_summaries.json"
    )


@lru_cache()
def get_path_settings() -> PathSettings:
    return PathSettings()
