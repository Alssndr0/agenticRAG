import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from enhance.summarise_chunks import summarise_chunk_contexts
from enhance.summarise_docs import summarise_documents
from utils.load_env import get_env_vars

# Load environment variables
ENV = get_env_vars()

# Input/output file paths
EXTRACTED_CHUNKS_FILE = ENV.get(
    "EXTRACTED_CHUNKS_FILE", "data/chunked/extracted_chunks.json"
)
ENHANCED_CHUNKS_FILE = ENV.get(
    "ENHANCED_CHUNKS_FILE", "data/enhanced/enhanced_chunks.json"
)


def run_pipeline():
    """
    Run the enhance pipeline to enrich chunks with document and chunk summaries.
    The pipeline:
    1. Loads extracted chunks
    2. Groups them by filename
    3. Generates document summaries
    4. Generates chunk summaries
    5. Adds summaries to chunk metadata
    6. Saves enhanced chunks
    """
    print("\n🚀 Starting enhance pipeline...")

    # Ensure the extracted chunks file exists
    if not os.path.exists(EXTRACTED_CHUNKS_FILE):
        print(f"Error: Extracted chunks file {EXTRACTED_CHUNKS_FILE} not found.")
        return False

    # Load the extracted chunks
    print(f"\n📄 Loading extracted chunks from {EXTRACTED_CHUNKS_FILE}...")
    try:
        with open(EXTRACTED_CHUNKS_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"  ✅ Loaded {len(chunks)} chunks")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Failed to load chunks from {EXTRACTED_CHUNKS_FILE}: {e}")
        return False

    # Group chunks by filename
    print("\n📑 Grouping chunks by filename...")
    chunks_by_filename = defaultdict(list)
    filenames = set()

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        filename = metadata.get("filename")

        # Handle both string and list cases for filename
        if isinstance(filename, list) and filename:
            filename = filename[0]  # Use the first filename if it's a list

        if filename:
            chunks_by_filename[filename].append(chunk)
            filenames.add(filename)

    print(f"  ✅ Found {len(filenames)} unique document files")

    # Extract full document texts for summarization
    print("\n📚 Preparing documents for summarization...")
    doc_filenames = list(filenames)
    full_docs = []

    for filename in doc_filenames:
        file_chunks = chunks_by_filename[filename]
        # Sort chunks by their idx if available
        file_chunks.sort(key=lambda x: x.get("idx", 0))
        # Combine all text from chunks into one document
        full_doc = " ".join(chunk.get("text", "") for chunk in file_chunks)
        full_docs.append(full_doc)

    # Create temporary files for the summarization process
    temp_dir = "data/enhanced"
    os.makedirs(temp_dir, exist_ok=True)

    # Save document filenames and full docs to temporary files
    doc_filenames_file = os.path.join(temp_dir, "temp_doc_filenames.json")
    full_docs_file = os.path.join(temp_dir, "temp_full_docs.json")

    with open(doc_filenames_file, "w", encoding="utf-8") as f:
        json.dump(doc_filenames, f, ensure_ascii=False)

    with open(full_docs_file, "w", encoding="utf-8") as f:
        json.dump(full_docs, f, ensure_ascii=False)

    # Generate document summaries
    print("\n📝 Generating document summaries...")
    doc_summaries_file = summarise_documents(
        doc_filenames_file=doc_filenames_file, full_docs_file=full_docs_file
    )

    # Load document summaries
    with open(doc_summaries_file, "r", encoding="utf-8") as f:
        doc_summaries = json.load(f)
    print(f"  ✅ Generated summaries for {len(doc_summaries)} documents")

    # Prepare data for chunk summarization
    # Convert chunks_by_filename to format expected by summarise_chunk_contexts
    # (text strings, not full chunk objects)
    merged_chunks_by_filename = {}
    for filename, file_chunks in chunks_by_filename.items():
        # Sort chunks by their idx
        file_chunks.sort(key=lambda x: x.get("idx", 0))
        # Extract just the text content
        merged_chunks_by_filename[filename] = [
            chunk.get("text", "") for chunk in file_chunks
        ]

    # Save merged chunks to a temporary file
    merged_chunks_file = os.path.join(temp_dir, "temp_merged_chunks.json")
    with open(merged_chunks_file, "w", encoding="utf-8") as f:
        json.dump(merged_chunks_by_filename, f, ensure_ascii=False)

    # Generate chunk summaries
    print("\n🔍 Generating chunk-level summaries...")
    chunk_summaries_file = summarise_chunk_contexts(
        doc_filenames_file=doc_filenames_file,
        summaries_file=doc_summaries_file,
        merged_chunks_file=merged_chunks_file,
    )

    # Load chunk summaries
    with open(chunk_summaries_file, "r", encoding="utf-8") as f:
        chunk_summaries_by_filename = json.load(f)

    total_chunk_summaries = sum(
        len(summaries) for summaries in chunk_summaries_by_filename.values()
    )
    print(f"  ✅ Generated {total_chunk_summaries} chunk summaries")

    # Add summaries to chunk metadata
    print("\n✨ Adding summaries to chunk metadata...")
    enhanced_chunks = []

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        filename = metadata.get("filename")

        # Handle both string and list cases for filename
        if isinstance(filename, list) and filename:
            filename = filename[0]  # Use the first filename in the list

        if filename:
            # Add document summary
            doc_summary = doc_summaries.get(filename, "")
            metadata["document_summary"] = doc_summary

            # Add chunk summary if available
            if filename in chunk_summaries_by_filename:
                # Find the corresponding chunk summary based on idx
                idx = chunk.get("idx", -1)
                # If idx is within the range of available summaries, use it
                if 0 <= idx < len(chunk_summaries_by_filename[filename]):
                    metadata["chunk_summary"] = chunk_summaries_by_filename[filename][
                        idx
                    ]
                else:
                    metadata["chunk_summary"] = ""
            else:
                metadata["chunk_summary"] = ""

        # Create enhanced chunk with updated metadata
        enhanced_chunk = {
            "idx": chunk.get("idx", 0),
            "text": chunk.get("text", ""),
            "metadata": metadata,
        }

        enhanced_chunks.append(enhanced_chunk)

    # Save enhanced chunks
    os.makedirs(os.path.dirname(ENHANCED_CHUNKS_FILE), exist_ok=True)
    with open(ENHANCED_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(enhanced_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Enhanced chunks written to {ENHANCED_CHUNKS_FILE}")

    # Clean up temporary files
    try:
        os.remove(doc_filenames_file)
        os.remove(full_docs_file)
        os.remove(merged_chunks_file)
    except:
        pass

    print("\n✅ Enhance pipeline completed successfully!")
    return True


if __name__ == "__main__":
    run_pipeline()
