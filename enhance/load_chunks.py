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


def group_by_filename(
    chunks: List[Any], metadata: List[Dict]
) -> Tuple[Dict[str, List[Any]], Dict[str, List[Dict]]]:
    """
    Groups chunks and metadata based on the 'filename' key in the metadata.

    Handles cases where the 'filename' value might be a single string or a list
    of strings (e.g., after merging documents).

    Args:
        chunks: A list of chunks (content).
        metadata: A list of metadata dictionaries. Each dictionary is expected
                  to have a 'filename' key.

    Returns:
        A tuple containing two dictionaries:
        1. grouped_chunks: A dictionary where keys are filenames and values
           are lists of chunks associated with that filename.
        2. grouped_metadata: A dictionary where keys are filenames and values
           are lists of metadata dictionaries associated with that filename.

    Raises:
        KeyError: If a metadata dictionary is missing the 'filename' key.
        TypeError: If a 'filename' value is neither a string nor a list.
    """
    grouped_chunks = defaultdict(list)
    grouped_metadata = defaultdict(list)

    if len(chunks) != len(metadata):
        raise ValueError(
            f"Input lists have different lengths: chunks ({len(chunks)}), metadata ({len(metadata)})"
        )

    for chunk, meta in zip(chunks, metadata):
        # Get filename(s) from metadata, ensuring it's always a list
        try:
            filenames_val = meta["filename"]
        except KeyError:
            print(f"Error: Metadata item missing 'filename' key: {meta}")
            raise  # Re-raise the KeyError

        if isinstance(filenames_val, list):
            filenames = filenames_val
        elif isinstance(filenames_val, str):
            filenames = [filenames_val]
        else:
            raise TypeError(
                f"Unexpected type for 'filename' in metadata: {type(filenames_val)}. Expected str or list. Metadata: {meta}"
            )

        # Add chunk and metadata to groups for each associated filename
        for fname in filenames:
            if not isinstance(fname, str):
                raise TypeError(
                    f"Expected filename to be a string, but got {type(fname)} in list: {filenames}. Metadata: {meta}"
                )
            grouped_chunks[fname].append(chunk)
            grouped_metadata[fname].append(meta)  # Append the original meta dict

    # Convert defaultdicts to regular dicts for the return value
    return dict(grouped_chunks), dict(grouped_metadata)
