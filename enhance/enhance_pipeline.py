import os
import sys

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from finalise_chunks import export_enriched_chunks_and_metadata
from load_chunks import load_chunks_and_metadata
from merge_chunks import build_full_docs, group_by_filename, merge_small_chunks
from summarise_chunks import summarise_chunk_contexts
from summarise_docs import summarise_documents

from utils.load_env import get_env_vars

# Get environment variables
env_vars = get_env_vars()
CHUNKS_FILE = env_vars.get("CHUNKS_FILE", "data/chunked/chunks.json")
METADATA_FILE = env_vars.get("METADATA_FILE", "data/chunked/metadata.json")
ENHANCED_CHUNKS_FILE = env_vars.get(
    "ENHANCED_CHUNKS_FILE", "data/enhanced/final_chunks.json"
)
ENHANCED_METADATA_FILE = env_vars.get(
    "ENHANCED_METADATA_FILE", "data/enhanced/final_metadata.json"
)

# Create output directories
os.makedirs(os.path.dirname(ENHANCED_CHUNKS_FILE), exist_ok=True)
os.makedirs(os.path.dirname(ENHANCED_METADATA_FILE), exist_ok=True)


def main():
    """
    Process chunks through the enhancement pipeline, writing to files at each step.
    Each step reads from the files produced by the previous step, making the process
    more resilient to failures.
    """
    print("\n🔄 Starting enhancement pipeline...\n")

    # Step 1: Load the chunks and metadata from the chunking process
    print("\n📦 Step 1: Loading chunks and metadata")
    chunks, metadata = load_chunks_and_metadata(CHUNKS_FILE, METADATA_FILE)
    print(f"✅ Loaded {len(chunks)} chunks and metadata entries")

    # Step 2: Group the chunks by filename and write to files
    print("\n📦 Step 2: Grouping chunks by filename")
    grouped_chunks_file, grouped_metadata_file = group_by_filename(chunks, metadata)
    print(f"✅ Grouped chunks written to {grouped_chunks_file}")
    print(f"✅ Grouped metadata written to {grouped_metadata_file}")

    # Step 3: Merge small chunks to meet minimum size requirements
    print("\n📦 Step 3: Merging small chunks")
    merged_chunks_file, merged_metadata_file = merge_small_chunks(
        grouped_chunks_file, grouped_metadata_file
    )
    print(f"✅ Merged chunks written to {merged_chunks_file}")
    print(f"✅ Merged metadata written to {merged_metadata_file}")

    # Step 4: Build full documents for summarization
    print("\n📦 Step 4: Building full documents")
    full_docs_file, doc_filenames_file = build_full_docs(merged_chunks_file)
    print(f"✅ Full documents written to {full_docs_file}")
    print(f"✅ Document filenames written to {doc_filenames_file}")

    # Step 5: Summarize the documents
    print("\n📦 Step 5: Summarizing documents")
    doc_summaries_file = summarise_documents(doc_filenames_file, full_docs_file)
    print(f"✅ Document summaries written to {doc_summaries_file}")

    # Step 6: Summarize the chunks with contextual information
    print("\n📦 Step 6: Summarizing chunks with context")
    chunk_summaries_file = summarise_chunk_contexts(
        doc_filenames_file, doc_summaries_file, merged_chunks_file
    )
    print(f"✅ Chunk context summaries written to {chunk_summaries_file}")

    # Step 7: Export the enriched chunks and metadata
    print("\n📦 Step 7: Finalizing enriched chunks and metadata")
    final_chunks_file, final_metadata_file = export_enriched_chunks_and_metadata(
        doc_summaries_file,
        chunk_summaries_file,
        merged_chunks_file,
        merged_metadata_file,
        ENHANCED_CHUNKS_FILE,
        ENHANCED_METADATA_FILE,
    )
    print(f"✅ Enriched chunks written to {final_chunks_file}")
    print(f"✅ Enriched metadata written to {final_metadata_file}")

    print("\n✅ Enhancement pipeline complete!")


if __name__ == "__main__":
    main()
