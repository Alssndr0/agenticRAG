from functools import lru_cache
from pathlib import Path

from app.configs.base_config import BASE_DIR, BaseConfig, get_base_config
from pydantic import Field


class ChunkConfig(BaseConfig):
    model_config = {"env_file": get_base_config().CHUNK_CONFIG_FILE}


class ChunkSettings(ChunkConfig):
    # Input/Output folders
    INPUT_FOLDER: Path = Field(default=BASE_DIR / "data/test")
    OUTPUT_FOLDER: Path = Field(default=BASE_DIR / "data/chunked")
    CHUNK_SIZE: int = 400
    MIN_WORDS: int = 200
    EXTRACTED_CHUNKS_FILE: Path = Field(
        default=BASE_DIR / "data/chunked/extracted_chunks.json"
    )
    EMBEDDINGS_FILE: Path = Field(default=BASE_DIR / "data/chunked/embeddings.npz")
    GROUPED_CHUNKS_FILE: Path = Field(
        default=BASE_DIR / "data/enhanced/grouped_chunks.json"
    )
    MERGED_CHUNKS_FILE: Path = Field(
        default=BASE_DIR / "data/enhanced/merged_chunks.json"
    )
    FULL_DOCS_FILE: Path = Field(default=BASE_DIR / "data/enhanced/full_docs.json")
    DOC_FILENAMES_FILE: Path = Field(
        default=BASE_DIR / "data/enhanced/doc_filenames.json"
    )
    ENHANCED_CHUNKS_FILE: Path = Field(
        default=BASE_DIR / "data/enhanced/enhanced_chunks.json"
    )


@lru_cache()
def get_chunk_settings() -> ChunkSettings:
    return ChunkSettings()
