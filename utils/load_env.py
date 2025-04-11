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
        "EMBED_MODEL_ID": os.getenv(
            "EMBED_MODEL_ID", "Alibaba-NLP/gte-Qwen2-7B-instruct"
        ),
        # Extraction related files
        "CHUNKS_FILE": os.getenv("CHUNKS_FILE", "data/chunked/chunks.json"),
        "METADATA_FILE": os.getenv("METADATA_FILE", "data/chunked/metadata.json"),
        # Enhancement intermediate files
        "GROUPED_CHUNKS_FILE": os.getenv(
            "GROUPED_CHUNKS_FILE", "data/enhanced/grouped_chunks.json"
        ),
        "GROUPED_METADATA_FILE": os.getenv(
            "GROUPED_METADATA_FILE", "data/enhanced/grouped_metadata.json"
        ),
        "MERGED_CHUNKS_FILE": os.getenv(
            "MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json"
        ),
        "MERGED_METADATA_FILE": os.getenv(
            "MERGED_METADATA_FILE", "data/enhanced/merged_metadata.json"
        ),
        "FULL_DOCS_FILE": os.getenv("FULL_DOCS_FILE", "data/enhanced/full_docs.json"),
        "DOC_FILENAMES_FILE": os.getenv(
            "DOC_FILENAMES_FILE", "data/enhanced/doc_filenames.json"
        ),
        # Summarization related variables
        "SUMMARISE_OUTPUT_FOLDER": os.getenv(
            "SUMMARISE_OUTPUT_FOLDER", "data/enhanced"
        ),
        "SUMMARISE_OUTPUT_FILE": os.getenv(
            "SUMMARISE_OUTPUT_FILE", "data/enhanced/document_summaries.txt"
        ),
        "SUMMARISE_DOCUMENT_PROMPT": os.getenv(
            "SUMMARISE_DOCUMENT_PROMPT",
            "Give a short succinct description of the overall document for the purposes of improving search retrieval.",
        ),
        "SUMMARISE_DOCUMENT_INPUT_WORDS": int(
            os.getenv("SUMMARISE_DOCUMENT_INPUT_WORDS", "5000")
        ),
        "SUMMARISE_MODEL": os.getenv("SUMMARISE_MODEL", "gpt-4o"),
        "SUMMARISE_CHUNK_PROMPT": os.getenv(
            "SUMMARISE_CHUNK_PROMPT",
            "Provide only a very short, succinct context summary for the target text to improve its searchability. Start with This chunk details...",
        ),
        "SUMMARISE_CHUNK_OUTPUT_FILE": os.getenv(
            "SUMMARISE_CHUNK_OUTPUT_FILE", "data/enhanced/chunk_context_summaries.txt"
        ),
        # Final enhanced output files
        "ENHANCED_CHUNKS_FILE": os.getenv(
            "ENHANCED_CHUNKS_FILE", "data/enhanced/final_chunks.json"
        ),
        "ENHANCED_METADATA_FILE": os.getenv(
            "ENHANCED_METADATA_FILE", "data/enhanced/final_metadata.json"
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
