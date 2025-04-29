import json
import os
from utils.load_env import get_env_vars

# Load every path from the centralised env loader
ENV = get_env_vars()
EXTRACTED_CHUNKS_FILE = ENV["EXTRACTED_CHUNKS_FILE"]
CHUNKS_FILE = ENV["CHUNKS_FILE"]
METADATA_FILE = ENV["METADATA_FILE"]


def write_chunks_json(new_chunks, append=True, use_legacy=False):
    """
    Write chunks and metadata to JSON files, using only env-configured paths.

    Args:
        new_chunks: List of dicts with keys 'text' and 'metadata'
        append: Whether to append to existing unified file
        use_legacy: Also write separate legacy chunk & metadata files
    """
    # Ensure output dir exists for unified file
    os.makedirs(os.path.dirname(EXTRACTED_CHUNKS_FILE), exist_ok=True)

    unified = []
    if append and os.path.exists(EXTRACTED_CHUNKS_FILE):
        try:
            with open(EXTRACTED_CHUNKS_FILE, "r", encoding="utf-8") as f:
                unified = json.load(f)
            next_idx = max((c.get("idx", -1) for c in unified), default=-1) + 1
        except (json.JSONDecodeError, FileNotFoundError):
            unified = []
            next_idx = 0
    else:
        next_idx = 0

    # Assign sequential idx and build unified list
    for i, chunk in enumerate(new_chunks):
        entry = {
            "idx": next_idx + i,
            "text": chunk["text"],
            "metadata": chunk["metadata"],
        }
        unified.append(entry)

    # Write unified file
    with open(EXTRACTED_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)
    print(f"Unified chunks written to {EXTRACTED_CHUNKS_FILE}")

    # Backwards-compat: separate files
    if use_legacy:
        os.makedirs(os.path.dirname(CHUNKS_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

        texts    = [c["text"]     for c in unified]
        metas    = [c["metadata"] for c in unified]

        with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
            json.dump(texts, f, ensure_ascii=False, indent=2)
        print(f"Legacy chunks written to {CHUNKS_FILE}")

        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metas, f, ensure_ascii=False, indent=2)
        print(f"Legacy metadata written to {METADATA_FILE}")


def write_unified_chunks(new_chunks, append=True):
    """
    Convenience wrapper for writing only the unified JSON.
    """
    write_chunks_json(new_chunks, append=append, use_legacy=False)
