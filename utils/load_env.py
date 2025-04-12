import os

from dotenv import load_dotenv


def load_env_vars():
    """Load environment variables from .env file and return a dict of common settings."""
    load_dotenv()

    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "OPENAI_API_URL": os.getenv(
            "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
        ),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "OPENAI_MAX_TOKENS": int(os.getenv("OPENAI_MAX_TOKENS", "1200")),
        "VLM_PROMPT": os.getenv("VLM_PROMPT", ""),
        "INPUT_FOLDER": os.getenv("INPUT_FOLDER", "data/test"),
        "OUTPUT_FOLDER": os.getenv("OUTPUT_FOLDER", "data/chunked"),
        "CHUNK_SIZE": os.getenv("CHUNK_SIZE", "400"),
        "MIN_WORDS": os.getenv("MIN_WORDS", "200"),
        "EMBED_MODEL_ID": os.getenv(
            "EMBED_MODEL_ID", "Alibaba-NLP/gte-Qwen2-7B-instruct"
        ),
        # Extraction output file (unified format with merging)
        "EXTRACTED_CHUNKS_FILE": os.getenv(
            "EXTRACTED_CHUNKS_FILE", "data/chunked/extracted_chunks.json"
        ),
        # Legacy extraction files (maintained for backward compatibility)
        "CHUNKS_FILE": os.getenv("CHUNKS_FILE", "data/chunked/chunks.json"),
        "METADATA_FILE": os.getenv("METADATA_FILE", "data/chunked/metadata.json"),
        # Embeddings output file
        "EMBEDDINGS_FILE": os.getenv("EMBEDDINGS_FILE", "data/chunked/embeddings.npz"),
        # Summarization related variables
        "SUMMARISE_MODEL": os.getenv("SUMMARISE_MODEL", "gpt-4o"),
        "SUMMARISE_DOCUMENT_PROMPT": os.getenv(
            "SUMMARISE_DOCUMENT_PROMPT",
            "Give a short succinct description of the overall document for the purposes of improving search retrieval.",
        ),
        "SUMMARISE_DOCUMENT_INPUT_WORDS": int(
            os.getenv("SUMMARISE_DOCUMENT_INPUT_WORDS", "5000")
        ),
        "SUMMARISE_CHUNK_PROMPT": os.getenv(
            "SUMMARISE_CHUNK_PROMPT",
            "Provide only a very short, succinct context summary for the target text to improve its searchability. Start with This chunk details...",
        ),
        "SUMMARISE_CHUNK_MODEL_MAX_INPUT_TOKENS": os.getenv(
            "SUMMARISE_CHUNK_MODEL_MAX_INPUT_TOKENS", "1000"
        ),
    }


# Singleton-like pattern - load once when module is imported
ENV_VARS = load_env_vars()


def get_env_vars(force_reload=False):
    """Get the loaded environment variables."""
    global ENV_VARS
    if force_reload:
        print("Reloading environment variables")
        ENV_VARS = load_env_vars()
    return ENV_VARS
