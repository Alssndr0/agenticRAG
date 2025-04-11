import json
from collections import defaultdict
from typing import Any, List, Tuple


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


def load_enhanced_chunks(chunks_file):
    """
    Load the enhanced chunks from the JSON file.

    Args:
        chunks_file (str): Path to the enhanced chunks JSON file (usually final_chunks.json)

    Returns:
        list: A list of dictionaries containing text chunks with their source file information
    """
    import json

    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"✅ Loaded {len(chunks)} enhanced chunks from {chunks_file}")
        return chunks
    except Exception as e:
        print(f"❌ Error loading enhanced chunks from {chunks_file}: {e}")
        return []


def load_enhanced_chunks_by_source(chunks_file):
    """
    Load the enhanced chunks and organize them by source file.

    Args:
        chunks_file (str): Path to the enhanced chunks JSON file (usually final_chunks.json)

    Returns:
        dict: A dictionary with source filenames as keys and lists of chunk text as values
    """
    import json

    chunks_by_source = defaultdict(list)

    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        for chunk in chunks:
            source_file = chunk.get("source_file", "unknown")
            chunks_by_source[source_file].append(chunk.get("text", ""))

        print(
            f"✅ Loaded chunks for {len(chunks_by_source)} sources from {chunks_file}"
        )
        return dict(chunks_by_source)
    except Exception as e:
        print(f"❌ Error loading enhanced chunks from {chunks_file}: {e}")
        return {}
