import json
import os

from utils.load_env import get_env_vars

env_vars = get_env_vars()
CHUNKS_FILE = env_vars.get("CHUNKS_FILE", "exports/chunks.json")
METADATA_FILE = env_vars.get("METADATA_FILE", "exports/metadata.json")


def write_chunks_json(
    new_chunks, chunks_path=CHUNKS_FILE, metadata_path=METADATA_FILE, append=True
):
    """
    Write chunks and metadata to JSON files, either appending to existing files or creating new ones.

    Args:
        new_chunks: List of new chunks to write
        chunks_path: Path to the chunks JSON file
        metadata_path: Path to the metadata JSON file
        append: Whether to append to existing files or create new ones
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(chunks_path), exist_ok=True)
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)

    # Extract chunk data and metadata
    chunks_data = [item["chunk"] for item in new_chunks]
    metadata_data = [item["metadata"] for item in new_chunks]

    # If appending and files exist, read existing data first
    if append and os.path.exists(chunks_path) and os.path.exists(metadata_path):
        try:
            with open(chunks_path, "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)
            with open(metadata_path, "r", encoding="utf-8") as f:
                existing_metadata = json.load(f)

            # Get the next ID to use
            next_id = max([m.get("id", 0) for m in existing_metadata], default=-1) + 1

            # Assign sequential IDs to new metadata starting from next_id
            for i, meta in enumerate(metadata_data):
                meta["id"] = next_id + i

            # Combine existing and new data
            chunks_data = existing_chunks + chunks_data
            metadata_data = existing_metadata + metadata_data
        except (json.JSONDecodeError, FileNotFoundError):
            # If files are empty or corrupt, treat as new files
            # Assign sequential IDs starting from 0
            for i, meta in enumerate(metadata_data):
                meta["id"] = i
    else:
        # Assign sequential IDs starting from 0
        for i, meta in enumerate(metadata_data):
            meta["id"] = i

    # Save chunks
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    print(f"Chunks written to {chunks_path}")

    # Save metadata
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_data, f, ensure_ascii=False, indent=2)
    print(f"Metadata written to {metadata_path}")
