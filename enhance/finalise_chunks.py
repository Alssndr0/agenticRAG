import json
import os

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
FINAL_CHUNKS_FILE = ENV.get("FINAL_CHUNKS_FILE", "data/enhanced/final_chunks.json")
MERGED_CHUNKS_FILE = ENV.get("MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json")
SUMMARISE_OUTPUT_FILE = ENV.get(
    "SUMMARISE_OUTPUT_FILE", "data/enhanced/doc_summaries.json"
)
SUMMARISE_CHUNK_OUTPUT_FILE = ENV.get(
    "SUMMARISE_CHUNK_OUTPUT_FILE", "data/enhanced/chunk_summaries.json"
)


def finalise_chunks(
    merged_chunks_file=MERGED_CHUNKS_FILE,
    output_file=FINAL_CHUNKS_FILE,
    doc_summaries_file=SUMMARISE_OUTPUT_FILE,
    chunk_summaries_file=SUMMARISE_CHUNK_OUTPUT_FILE,
):
    """
    Process the merged chunks and prepare them for embedding by:
    1. Flattening the grouped structure into a list
    2. Adding unique IDs and positional information
    3. Incorporating document and chunk summaries
    4. Ensuring all required fields are present

    Args:
        merged_chunks_file (str): Path to JSON file containing merged chunks grouped by filename
        output_file (str): Output path for finalised chunks ready for embedding
        doc_summaries_file (str): Path to document summaries JSON file
        chunk_summaries_file (str): Path to chunk summaries JSON file

    Returns:
        str: Path to the output file containing finalised chunks
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load merged chunks
    try:
        with open(merged_chunks_file, "r", encoding="utf-8") as f:
            grouped_chunks = json.load(f)
        print(f"✅ Loaded merged chunks from {merged_chunks_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading merged chunks from {merged_chunks_file}: {e}")
        return None

    # Load document summaries if available
    doc_summaries = {}
    try:
        with open(doc_summaries_file, "r", encoding="utf-8") as f:
            doc_summaries = json.load(f)
        print(f"✅ Loaded document summaries from {doc_summaries_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(
            f"⚠️ Warning: Could not load document summaries from {doc_summaries_file}: {e}"
        )
        print("  Will proceed without document summaries.")

    # Load chunk summaries if available
    chunk_summaries = {}
    try:
        with open(chunk_summaries_file, "r", encoding="utf-8") as f:
            chunk_summaries = json.load(f)
        print(f"✅ Loaded chunk summaries from {chunk_summaries_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(
            f"⚠️ Warning: Could not load chunk summaries from {chunk_summaries_file}: {e}"
        )
        print("  Will proceed without chunk summaries.")

    # Flatten and enrich chunks
    final_chunks = []
    processed_files = 0
    total_chunks = 0

    for filename, chunks in grouped_chunks.items():
        processed_files += 1
        file_chunks = 0

        # Get document summary for this file if available
        doc_summary = doc_summaries.get(filename, "")

        # Get chunk summaries for this file if available
        file_chunk_summaries = chunk_summaries.get(filename, [])

        for chunk_idx, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                print(
                    f"⚠️ Warning: Chunk is not a dictionary in file '{filename}' at index {chunk_idx}. Skipping."
                )
                continue

            if "text" not in chunk:
                print(
                    f"⚠️ Warning: Missing 'text' field in chunk for file '{filename}' at index {chunk_idx}. Skipping."
                )
                continue

            # Get metadata, defaulting to empty dict
            metadata = chunk.get("metadata", {})

            # Create a unique ID for this chunk
            chunk_id = f"{filename}_{chunk_idx}"

            # Add document summary to metadata
            metadata["document_summary"] = doc_summary

            # Add chunk summary to metadata if available
            if chunk_idx < len(file_chunk_summaries):
                metadata["chunk_summary"] = file_chunk_summaries[chunk_idx]
            else:
                metadata["chunk_summary"] = ""

            # Add source file and position information to metadata
            metadata["source_file"] = filename
            metadata["chunk_index"] = chunk_idx
            metadata["chunk_id"] = chunk_id

            # Ensure the structure follows the expected format
            finalised_chunk = {
                "idx": chunk.get("idx", chunk_idx),  # Use original idx if available
                "text": chunk["text"],
                "metadata": metadata,
            }

            final_chunks.append(finalised_chunk)
            file_chunks += 1
            total_chunks += 1

        print(f"  Processed file: {filename} ({file_chunks} chunks)")

    # Write output file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_chunks, f, ensure_ascii=False, indent=2)
        print(f"✅ Finalised chunks written to {output_file}")
        print(f"\nProcessed {processed_files} files with {total_chunks} total chunks")
    except IOError as e:
        print(f"❌ Error writing finalised chunks to {output_file}: {e}")
        return None

    return output_file
