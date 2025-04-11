import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from utils.load_env import get_env_vars

ENV = get_env_vars()
GROUPED_CHUNKS_FILE = ENV.get(
    "GROUPED_CHUNKS_FILE", "data/enhanced/grouped_chunks.json"
)
GROUPED_METADATA_FILE = ENV.get(
    "GROUPED_METADATA_FILE", "data/enhanced/grouped_metadata.json"
)
MERGED_CHUNKS_FILE = ENV.get("MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json")
MERGED_METADATA_FILE = ENV.get(
    "MERGED_METADATA_FILE", "data/enhanced/merged_metadata.json"
)
FULL_DOCS_FILE = ENV.get("FULL_DOCS_FILE", "data/enhanced/full_docs.json")
DOC_FILENAMES_FILE = ENV.get("DOC_FILENAMES_FILE", "data/enhanced/doc_filenames.json")


def group_by_filename(chunks: List[Any], metadata: List[Dict]) -> Tuple[str, str]:
    """
    Group chunks and their metadata by filename.

    Args:
        chunks: List of chunks.
        metadata: List of metadata entries.

    Returns:
        Tuple containing paths to the output files (chunks_path, metadata_path).
    """
    # Create defaultdicts to group by filename
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

    print("📄 Documents found:", list(grouped_chunks.keys()))

    for filename in grouped_chunks:
        print(f"\n--- {filename} ---")
        print(f"Chunks: {len(grouped_chunks[filename])}")
        print(f"Metadata entries: {len(grouped_metadata[filename])}")

    # Count words in each chunk
    word_counts = [len(chunk.split()) for chunk in chunks]
    # Print summary
    for i, count in enumerate(word_counts):
        print(f"Chunk {i}: {count} words")

    # Ensure directories exist
    os.makedirs(os.path.dirname(GROUPED_CHUNKS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(GROUPED_METADATA_FILE), exist_ok=True)

    # Convert defaultdicts to regular dicts for JSON serialization
    grouped_chunks_dict = {k: v for k, v in grouped_chunks.items()}
    grouped_metadata_dict = {k: v for k, v in grouped_metadata.items()}

    # Write to files
    with open(GROUPED_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(grouped_chunks_dict, f, ensure_ascii=False, indent=2)

    with open(GROUPED_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(grouped_metadata_dict, f, ensure_ascii=False, indent=2)

    print(f"✅ Grouped chunks written to {GROUPED_CHUNKS_FILE}")
    print(f"✅ Grouped metadata written to {GROUPED_METADATA_FILE}")

    return GROUPED_CHUNKS_FILE, GROUPED_METADATA_FILE


def to_list(x):
    return x if isinstance(x, list) else [x]


def count_words(text):
    """Count words in a text string."""
    return len(text.split())


def merge_metadata(meta1, meta2):
    """
    Merge two metadata dictionaries.
    If values are incompatible types, keep both as a list.
    Deduplicates values in lists and maintains relationships between
    bounding boxes, charspans, and their respective pages.
    """
    merged = {}
    all_keys = set(meta1.keys()) | set(meta2.keys())

    # Special handling for document properties
    special_keys = {"filename", "id", "pages"}

    for key in all_keys:
        val1 = meta1.get(key)
        val2 = meta2.get(key)

        if val1 is None:
            merged[key] = val2
        elif val2 is None:
            merged[key] = val1
        elif key in special_keys:
            # Handle document properties (filename, id, pages)
            if isinstance(val1, list) and isinstance(val2, list):
                # Combine and deduplicate
                merged[key] = list(dict.fromkeys(val1 + val2))
            elif isinstance(val1, list):
                # Add val2 to val1 list and deduplicate
                merged[key] = list(dict.fromkeys(val1 + [val2]))
            elif isinstance(val2, list):
                # Add val1 to val2 list and deduplicate
                merged[key] = list(dict.fromkeys([val1] + val2))
            elif val1 == val2:
                # Keep one if they're the same
                merged[key] = val1
            else:
                # Store both as a deduplicated list
                merged[key] = list(dict.fromkeys([val1, val2]))
        elif key == "bounding_boxes" or key == "charspans":
            # For bounding boxes and charspans, we need to preserve their relationship
            # with pages, so we need to be careful when merging
            if not merged.get("page_mappings"):
                merged["page_mappings"] = {}

            # Create or get page_mappings for this element type
            if f"{key}_page_map" not in merged["page_mappings"]:
                merged["page_mappings"][f"{key}_page_map"] = {}

            # Combine the lists
            if isinstance(val1, list) and isinstance(val2, list):
                merged[key] = val1 + val2

                # Map the elements to their pages
                pages1 = meta1.get("pages", [])
                pages2 = meta2.get("pages", [])

                # Store mapping if we have page information
                if pages1 and isinstance(pages1, list):
                    for i, box in enumerate(val1):
                        # Associate with the correct page if possible
                        page_idx = i % len(pages1) if len(pages1) > 0 else 0
                        page = pages1[page_idx]
                        merged["page_mappings"][f"{key}_page_map"][len(val1) + i] = page

                if pages2 and isinstance(pages2, list):
                    for i, box in enumerate(val2):
                        # Associate with the correct page if possible
                        page_idx = i % len(pages2) if len(pages2) > 0 else 0
                        page = pages2[page_idx]
                        merged["page_mappings"][f"{key}_page_map"][len(val1) + i] = page
            else:
                # Handle non-list values - convert to list
                merged[key] = [val1, val2] if val1 != val2 else [val1]
        elif key == "headings":
            # For headings, deduplicate while preserving order
            if isinstance(val1, list) and isinstance(val2, list):
                # Use dict.fromkeys to preserve order while deduplicating
                merged[key] = list(dict.fromkeys(val1 + val2))
            elif isinstance(val1, list):
                merged[key] = list(dict.fromkeys(val1 + [val2]))
            elif isinstance(val2, list):
                merged[key] = list(dict.fromkeys([val1] + val2))
            elif val1 == val2:
                merged[key] = val1
            else:
                merged[key] = [val1, val2]
        elif isinstance(val1, list) and isinstance(val2, list):
            # For other lists, deduplicate while preserving order
            merged[key] = list(dict.fromkeys(val1 + val2))
        elif isinstance(val1, list):
            # Add val2 to val1 list and deduplicate
            merged[key] = list(dict.fromkeys(val1 + [val2]))
        elif isinstance(val2, list):
            # Add val1 to val2 list and deduplicate
            merged[key] = list(dict.fromkeys([val1] + val2))
        elif val1 == val2:
            # Keep one if they're the same
            merged[key] = val1
        else:
            # Otherwise, store both as a list
            merged[key] = [val1, val2]

    return merged


def merge_small_chunks(
    grouped_chunks_file=GROUPED_CHUNKS_FILE,
    grouped_metadata_file=GROUPED_METADATA_FILE,
    min_words=200,
):
    """
    Merge small chunks to meet minimum word count and write results to files.

    Args:
        grouped_chunks_file: Path to the JSON file with grouped chunks.
        grouped_metadata_file: Path to the JSON file with grouped metadata.
        min_words: Minimum number of words per chunk.

    Returns:
        Tuple of file paths (merged_chunks_file, merged_metadata_file).
    """
    # Ensure directories exist
    os.makedirs(os.path.dirname(MERGED_CHUNKS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(MERGED_METADATA_FILE), exist_ok=True)

    # Load grouped chunks and metadata from files
    with open(grouped_chunks_file, "r", encoding="utf-8") as f:
        grouped_chunks = json.load(f)

    with open(grouped_metadata_file, "r", encoding="utf-8") as f:
        grouped_metadata = json.load(f)

    merged_grouped_chunks = {}
    merged_grouped_metadata = {}

    for filename in grouped_chunks:
        chunks = grouped_chunks[filename]
        metadata = grouped_metadata[filename]

        merged = True
        while merged:
            merged = False
            new_chunks = []
            new_metadata = []
            i = 0

            while i < len(chunks):
                chunk = chunks[i]
                meta = metadata[i]
                word_count = count_words(chunk)

                if word_count >= min_words:
                    new_chunks.append(chunk)
                    new_metadata.append(meta)
                    i += 1
                else:
                    prev_len = count_words(chunks[i - 1]) if i > 0 else float("inf")
                    next_len = (
                        count_words(chunks[i + 1])
                        if i + 1 < len(chunks)
                        else float("inf")
                    )

                    if next_len <= prev_len and i + 1 < len(chunks):
                        # Merge with next
                        new_chunk = chunk + " " + chunks[i + 1]
                        new_meta = merge_metadata(meta, metadata[i + 1])
                        new_chunks.append(new_chunk)
                        new_metadata.append(new_meta)
                        i += 2
                        merged = True
                    elif i > 0:
                        # Merge with previous
                        new_chunks[-1] += " " + chunk
                        new_metadata[-1] = merge_metadata(new_metadata[-1], meta)
                        i += 1
                        merged = True
                    else:
                        # Nowhere to merge
                        new_chunks.append(chunk)
                        new_metadata.append(meta)
                        i += 1

            chunks = new_chunks
            metadata = new_metadata

        merged_grouped_chunks[filename] = chunks
        merged_grouped_metadata[filename] = metadata

    print("✅ Merging complete.")
    print(f"Documents processed: {len(merged_grouped_chunks)}")
    for filename, chunks in merged_grouped_chunks.items():
        print(f"\n📄 Document: {filename}")
        word_counts = [len(chunk.split()) for chunk in chunks]

        print(f"  ➤ Avg words: {sum(word_counts) / len(word_counts):.2f}")
        print(f"  ➤ Max words: {max(word_counts)}")
        print(f"  ➤ Min words: {min(word_counts)}")

    # Write merged chunks and metadata to files
    with open(MERGED_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_grouped_chunks, f, ensure_ascii=False, indent=2)

    with open(MERGED_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_grouped_metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ Merged chunks written to {MERGED_CHUNKS_FILE}")
    print(f"✅ Merged metadata written to {MERGED_METADATA_FILE}")

    return MERGED_CHUNKS_FILE, MERGED_METADATA_FILE


def build_full_docs(merged_chunks_file=MERGED_CHUNKS_FILE):
    """
    Combines chunks of text per document into full document strings and writes to files.

    Args:
        merged_chunks_file (str): Path to the JSON file containing merged chunks.

    Returns:
        tuple: (full_docs_file_path, doc_filenames_file_path)
    """
    # Ensure directories exist
    os.makedirs(os.path.dirname(FULL_DOCS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(DOC_FILENAMES_FILE), exist_ok=True)

    # Load merged chunks from file
    with open(merged_chunks_file, "r", encoding="utf-8") as f:
        merged_grouped_chunks = json.load(f)

    full_docs = []
    doc_filenames = []

    for filename, chunks in merged_grouped_chunks.items():
        full_text = " ".join(chunks)
        full_docs.append(full_text)
        doc_filenames.append(filename)

    print(f"\n✅ Built {len(full_docs)} full documents.")
    for i, (fname, doc) in enumerate(zip(doc_filenames, full_docs)):
        print(f"\n📄 Document {i + 1}: {fname}")
        print(f"  ➤ Total words: {len(doc.split())}")

    # Write full docs and filenames to files
    with open(FULL_DOCS_FILE, "w", encoding="utf-8") as f:
        json.dump(full_docs, f, ensure_ascii=False, indent=2)

    with open(DOC_FILENAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(doc_filenames, f, ensure_ascii=False, indent=2)

    print(f"✅ Full documents written to {FULL_DOCS_FILE}")
    print(f"✅ Document filenames written to {DOC_FILENAMES_FILE}")

    return FULL_DOCS_FILE, DOC_FILENAMES_FILE
