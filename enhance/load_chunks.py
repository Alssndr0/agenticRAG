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


def load_enhanced_chunks_with_metadata(chunks_file, metadata_file):
    """
    Load both enhanced chunks and metadata and link them using chunk_id.

    Args:
        chunks_file (str): Path to the enhanced chunks JSON file (usually final_chunks.json)
        metadata_file (str): Path to the enhanced metadata JSON file (usually final_metadata.json)

    Returns:
        dict: A dictionary with chunk_ids as keys, and each value containing both
              the chunk text and its associated metadata
    """
    import json

    linked_data = {}

    # Load chunks
    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"✅ Loaded {len(chunks)} enhanced chunks from {chunks_file}")

        # Index chunks by chunk_id
        chunks_dict = {
            chunk.get("chunk_id", f"unknown_{i}"): chunk
            for i, chunk in enumerate(chunks)
        }
    except Exception as e:
        print(f"❌ Error loading enhanced chunks from {chunks_file}: {e}")
        return {}

    # Load metadata
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"✅ Loaded {len(metadata)} metadata entries from {metadata_file}")

        # Index metadata by chunk_id
        metadata_dict = {
            meta.get("chunk_id", f"unknown_{i}"): meta
            for i, meta in enumerate(metadata)
        }
    except Exception as e:
        print(f"❌ Error loading metadata from {metadata_file}: {e}")
        return chunks_dict  # Return just chunks if metadata loading fails

    # Link chunks with their metadata
    for chunk_id, chunk in chunks_dict.items():
        meta = metadata_dict.get(chunk_id)
        if meta:
            linked_data[chunk_id] = {"chunk": chunk, "metadata": meta}
        else:
            # If metadata not found, still include the chunk
            linked_data[chunk_id] = {"chunk": chunk, "metadata": None}

    print(f"✅ Linked {len(linked_data)} chunks with their metadata")
    return linked_data


def get_chunks_by_source_with_metadata(chunks_file, metadata_file):
    """
    Load chunks and metadata organized by source document.

    Args:
        chunks_file (str): Path to the enhanced chunks JSON file
        metadata_file (str): Path to the enhanced metadata JSON file

    Returns:
        dict: A dictionary with source filenames as keys, and each value containing
              a list of objects with both chunk text and metadata
    """
    from collections import defaultdict

    # First get the linked data
    linked_data = load_enhanced_chunks_with_metadata(chunks_file, metadata_file)

    # Organize by source file
    by_source = defaultdict(list)
    for chunk_id, data in linked_data.items():
        chunk = data["chunk"]
        source = chunk.get("source_file", "unknown")
        by_source[source].append(data)

    # Sort chunks within each source by chunk_index
    for source in by_source:
        by_source[source] = sorted(
            by_source[source], key=lambda x: x["chunk"].get("chunk_index", 0)
        )

    return dict(by_source)
