import json
import os

from utils.load_env import get_env_vars

env_vars = get_env_vars()
EXTRACTED_CHUNKS_FILE = env_vars.get(
    "EXTRACTED_CHUNKS_FILE", "data/chunked/extracted_chunks.json"
)
# Legacy variables maintained for backward compatibility
CHUNKS_FILE = env_vars.get("CHUNKS_FILE", "data/chunked/chunks.json")
METADATA_FILE = env_vars.get("METADATA_FILE", "data/chunked/metadata.json")


def write_chunks_json(
    new_chunks,
    unified_path=EXTRACTED_CHUNKS_FILE,
    append=True,
    use_legacy=False,
    chunks_path=CHUNKS_FILE,
    metadata_path=METADATA_FILE,
):
    """
    Write chunks and metadata to JSON files, either as a unified structure or in separate files.

    Args:
        new_chunks: List of new chunks to write (each containing 'idx', 'text', and 'metadata')
        unified_path: Path to the unified JSON file (containing both chunks and metadata)
        append: Whether to append to existing files or create new ones
        use_legacy: Whether to also write to separate chunks and metadata files (backward compatibility)
        chunks_path: Path to the legacy chunks JSON file
        metadata_path: Path to the legacy metadata JSON file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(unified_path), exist_ok=True)

    # Create unified chunk objects
    unified_chunks = []

    # If appending and file exists, read existing data first
    if append and os.path.exists(unified_path):
        try:
            with open(unified_path, "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)

            # Get the next idx to use
            next_idx = (
                max([chunk.get("idx", 0) for chunk in existing_chunks], default=-1) + 1
            )

            # Prepare to append new chunks
            unified_chunks = existing_chunks

            # Assign sequential idx values to new chunks starting from next_idx
            for i, chunk in enumerate(new_chunks):
                # Create a copy of the chunk to avoid modifying the input
                new_chunk = chunk.copy()
                new_chunk["idx"] = next_idx + i
                unified_chunks.append(new_chunk)

        except (json.JSONDecodeError, FileNotFoundError):
            # If file is empty or corrupt, treat as new file
            # Assign sequential idx values starting from 0
            for i, chunk in enumerate(new_chunks):
                # Create a copy of the chunk to avoid modifying the input
                new_chunk = chunk.copy()
                new_chunk["idx"] = i
                unified_chunks.append(new_chunk)
    else:
        # Assign sequential idx values starting from 0
        for i, chunk in enumerate(new_chunks):
            # Create a copy of the chunk to avoid modifying the input
            new_chunk = chunk.copy()
            new_chunk["idx"] = i
            unified_chunks.append(new_chunk)

    # Save unified chunks
    with open(unified_path, "w", encoding="utf-8") as f:
        json.dump(unified_chunks, f, ensure_ascii=False, indent=2)
    print(f"Unified chunks written to {unified_path}")

    # For backward compatibility, also write to separate files if requested
    if use_legacy:
        # Ensure legacy directories exist
        os.makedirs(os.path.dirname(chunks_path), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

        # Extract chunk data and metadata for the legacy format
        chunks_data = [item["text"] for item in unified_chunks]
        metadata_data = [item["metadata"] for item in unified_chunks]

        # Save chunks
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
        print(f"Legacy chunks written to {chunks_path}")

        # Save metadata
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata_data, f, ensure_ascii=False, indent=2)
        print(f"Legacy metadata written to {metadata_path}")


def write_unified_chunks(new_chunks, output_path=EXTRACTED_CHUNKS_FILE, append=True):
    """
    Simplified function to write chunks and metadata to a unified JSON file.

    Args:
        new_chunks: List of new chunks to write (each containing 'idx', 'text', and 'metadata')
        output_path: Path to the unified JSON file
        append: Whether to append to existing file or create a new one
    """
    return write_chunks_json(
        new_chunks, unified_path=output_path, append=append, use_legacy=False
    )
