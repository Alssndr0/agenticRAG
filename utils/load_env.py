import os
from dotenv import load_dotenv

def load_env_vars():
    """Load environment variables from .env file and return a dict of common settings."""
    load_dotenv()

    return {
        # OpenAI
        # "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        # "OPENAI_API_URL": os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"),
        # "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        # "OPENAI_MAX_TOKENS": int(os.getenv("OPENAI_MAX_TOKENS", "1200")),
        # "VLM_PROMPT": os.getenv("VLM_PROMPT", ""),

        # I/O folders
        # "INPUT_FOLDER": os.getenv("INPUT_FOLDER", "data/test"),
        # "OUTPUT_FOLDER": os.getenv("OUTPUT_FOLDER", "data/chunked"),

        # Chunking
        # "CHUNK_SIZE": os.getenv("CHUNK_SIZE", "400"),
        # "MIN_WORDS": os.getenv("MIN_WORDS", "200"),

        # Embeddings
        # "EMBED_MODEL_ID": os.getenv("EMBED_MODEL_ID", "Alibaba-NLP/gte-Qwen2-7B-instruct"),

        # Indexes Paths
        # "FAISS_INDEX_PATH": os.getenv("FAISS_INDEX_PATH", "indexes/FAISS-TEST/enhanced_chunks_20250412_193515"),
        # "BM25_INDEX_PATH": os.getenv("BM25_INDEX_PATH", "indexes/bm25/bm25_index_20250412_193515.pkl"),
        # "GRAPH_INDEX_PATH": os.getenv("GRAPH_INDEX_PATH", "data/indexes/graph_index"),

        # Extraction output files
        # "EXTRACTED_CHUNKS_FILE": os.getenv("EXTRACTED_CHUNKS_FILE", "data/chunked/extracted_chunks.json"),
        # "EMBEDDINGS_FILE": os.getenv("EMBEDDINGS_FILE", "data/chunked/embeddings.npz"),

        # Legacy output files
        # "CHUNKS_FILE": os.getenv("CHUNKS_FILE", "data/chunked/chunks.json"),
        # "METADATA_FILE": os.getenv("METADATA_FILE", "data/chunked/metadata.json"),

        # Enhanced output files
        # "GROUPED_CHUNKS_FILE": os.getenv("GROUPED_CHUNKS_FILE", "data/enhanced/grouped_chunks.json"),
        # "MERGED_CHUNKS_FILE": os.getenv("MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json"),
        # "FULL_DOCS_FILE": os.getenv("FULL_DOCS_FILE", "data/enhanced/full_docs.json"),
        # "DOC_FILENAMES_FILE": os.getenv("DOC_FILENAMES_FILE", "data/enhanced/doc_filenames.json"),
        # "ENHANCED_CHUNKS_FILE": os.getenv("ENHANCED_CHUNKS_FILE", "data/enhanced/enhanced_chunks.json"),

        # Summarization
        # "SUMMARISE_MODEL": os.getenv("SUMMARISE_MODEL", "gpt-4o-mini"),
        # "SUMMARISE_DOCUMENT_PROMPT": os.getenv(
        #     "SUMMARISE_DOCUMENT_PROMPT",
        #     "Give a short succinct description of the overall document for the purposes of improving search retrieval.",
        # ),
        # "SUMMARISE_DOCUMENT_INPUT_WORDS": int(os.getenv("SUMMARISE_DOCUMENT_INPUT_WORDS", "1000")),
        # "SUMMARISE_CHUNK_PROMPT": os.getenv(
        #     "SUMMARISE_CHUNK_PROMPT",
        #     "Provide only a very short, succinct context summary for the target text to improve its searchability. Start with 'This chunk details...'",
        # ),
        # "SUMMARISE_CHUNK_MODEL_MAX_INPUT_TOKENS": os.getenv("SUMMARISE_CHUNK_MODEL_MAX_INPUT_TOKENS", "1000"),
        # "SUMMARISE_OUTPUT_FILE": os.getenv("SUMMARISE_OUTPUT_FILE", "data/enhanced/doc_summaries.json"),
        # "SUMMARISE_CHUNK_OUTPUT_FILE": os.getenv("SUMMARISE_CHUNK_OUTPUT_FILE", "data/enhanced/chunk_summaries.json"),
                                                 
        #Neo4j
    #     "NEO4J_URI": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    #     "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME", "neo4j"),
    #     "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD", "password"),
    #     "NEO4J_FULLTEXT_INDEX_NAME": os.getenv("NEO4J_FULLTEXT_INDEX_NAME", "entityNames"),
    # }

# Singleton-like pattern - load once when module is imported
ENV_VARS = load_env_vars()

def get_env_vars(force_reload=False):
    """Get the loaded environment variables."""
    global ENV_VARS
    if force_reload:
        print("Reloading environment variables")
        ENV_VARS = load_env_vars()
    return ENV_VARS
