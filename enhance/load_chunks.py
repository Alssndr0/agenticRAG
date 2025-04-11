import json
from collections import defaultdict
from typing import Any, Dict, List, Tuple


def load_chunks_and_metadata(
    chunks_file_path: str, metadata_file_path: str
) -> Tuple[List[Any], List[Any]]:
    """
    Loads chunk data and metadata from specified JSON files.

    Args:
        chunks_file_path: The path to the JSON file containing the chunks.
        metadata_file_path: The path to the JSON file containing the metadata.

    Returns:
        A tuple containing two lists: (chunks, metadata).

    Raises:
        FileNotFoundError: If either input file path does not exist.
        json.JSONDecodeError: If either file is not valid JSON.
        AssertionError: If chunks or metadata is not a list, or if they
                        have different lengths.
    """
    # Load chunks
    try:
        with open(chunks_file_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except FileNotFoundError:
        print(f"Error: Chunks file not found at {chunks_file_path}")
        raise  # Re-raise the exception
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {chunks_file_path}")
        raise  # Re-raise the exception

    # Load metadata
    try:
        with open(metadata_file_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"Error: Metadata file not found at {metadata_file_path}")
        raise  # Re-raise the exception
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {metadata_file_path}")
        raise  # Re-raise the exception

    # Check if both are lists
    assert isinstance(chunks, list), f"{chunks_file_path} should contain a list"
    assert isinstance(metadata, list), f"{metadata_file_path} should contain a list"

    # Assert equal length
    assert len(chunks) == len(metadata), (
        f"Mismatch: {len(chunks)} chunks ({chunks_file_path}) vs {len(metadata)} metadata entries ({metadata_file_path})"
    )

    print(f"✅ Loaded {len(chunks)} chunks and metadata entries successfully.")

    return chunks, metadata



