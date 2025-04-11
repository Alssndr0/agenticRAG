import os
import sys

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from load_chunks import load_chunks_and_metadata
from merge_chunks import build_full_docs, group_by_filename, merge_small_chunks
from summarise_chunks import summarise_chunk_contexts
from summarise_docs import summarise_documents

from utils.load_env import get_env_vars

env_vars = get_env_vars()
CHUNKS_FILE = env_vars.get("CHUNKS_FILE", "exports/chunks.json")
METADATA_FILE = env_vars.get("METADATA_FILE", "exports/metadata.json")
# Load the chunks and metadata
chunks, metadata = load_chunks_and_metadata(CHUNKS_FILE, METADATA_FILE)

# Group the chunks by filename
grouped_chunks, grouped_metadata = group_by_filename(chunks, metadata)
# Merge the small chunks
merged_grouped_chunks, merged_grouped_metadata = merge_small_chunks(
    grouped_chunks, grouped_metadata
)
# Build the full documents
full_docs, doc_filenames = build_full_docs(merged_grouped_chunks)
# Summarise the documents
summarised_docs = summarise_documents(doc_filenames, full_docs)
# Summarise the chunks
summarised_chunks = summarise_chunk_contexts(
    doc_filenames, summarised_docs, merged_grouped_chunks
)
