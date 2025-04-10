import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import using relative imports for files in the same directory
from docling.chunking import HybridChunker
from extract_chunk_metadata import extract_all_chunks_metadata
from transformers import AutoTokenizer
from write_chunks import write_chunks_json

from extract import convert_pdf_with_vlm
from utils.load_env import get_env_vars

env_vars = get_env_vars()
INPUT_FOLDER = Path(env_vars["INPUT_FOLDER"])
OUTPUT_FOLDER = Path(env_vars["OUTPUT_FOLDER"])
MAX_TOKENS = int(env_vars["CHUNK_SIZE"])
EMBED_MODEL_ID = env_vars["EMBED_MODEL_ID"]
CHUNKS_FILE = env_vars.get("CHUNKS_FILE", "exports/chunks.json")
METADATA_FILE = env_vars.get("METADATA_FILE", "exports/metadata.json")

# Initialize chunker with tokenizer and max tokens
tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID)
chunker = HybridChunker(tokenizer=tokenizer, max_tokens=MAX_TOKENS, merge_peers=True)


# Process each PDF document one at a time
for input_doc_path in INPUT_FOLDER.glob("*.pdf"):
    print(f"Processing: {input_doc_path.name}")

    # Convert the document
    extraction = convert_pdf_with_vlm(input_doc_path)

    # Chunk the document
    document_chunks = list(chunker.chunk(dl_doc=extraction.document))

    # Process and format the chunks for storage
    processed_chunks = extract_all_chunks_metadata(document_chunks)

    # Write chunks to files after each document is processed
    write_chunks_json(processed_chunks)

print("Processing complete!")
