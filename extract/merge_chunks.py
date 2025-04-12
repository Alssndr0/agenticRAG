import json
import os
from collections import defaultdict

from utils.load_env import get_env_vars

ENV = get_env_vars()
EXTRACTED_CHUNKS_FILE = ENV.get(
    "EXTRACTED_CHUNKS_FILE", "data/chunked/extracted_chunks.json"
)
GROUPED_CHUNKS_FILE = ENV.get(
    "GROUPED_CHUNKS_FILE", "data/enhanced/grouped_chunks.json"
)
MERGED_CHUNKS_FILE = ENV.get("MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json")
FULL_DOCS_FILE = ENV.get("FULL_DOCS_FILE", "data/enhanced/full_docs.json")
DOC_FILENAMES_FILE = ENV.get("DOC_FILENAMES_FILE", "data/enhanced/doc_filenames.json")


def group_by_filename(extracted_chunks_file: str) -> str:
    """
    Group unified chunks by filename.

    Args:
        extracted_chunks_file: Path to the unified chunks JSON file.

    Returns:
        Path to the grouped chunks file.
    """
    # Create defaultdicts to group by filename
    grouped_chunks = defaultdict(list)

    # Load unified chunks
    try:
        with open(extracted_chunks_file, "r", encoding="utf-8") as f:
            unified_chunks = json.load(f)
            print(f"Loaded {len(unified_chunks)} chunks from {extracted_chunks_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading unified chunks from {extracted_chunks_file}: {e}")
        return None

    # Group chunks by filename
    for chunk in unified_chunks:
        # Get text from top level
        text = chunk.get("text", "")
        # Get metadata from the metadata field
        metadata = chunk.get("metadata", {})

        # Get filename(s) from metadata, ensuring it's always a list
        try:
            filename_val = metadata.get("filename")
            if filename_val is None:
                print(f"Error: Metadata missing 'filename' key: {metadata}")
                continue  # Skip this chunk
        except (KeyError, TypeError):
            print(f"Error: Problem accessing 'filename' in metadata: {metadata}")
            continue  # Skip this chunk

        if isinstance(filename_val, list):
            filenames = filename_val
        elif isinstance(filename_val, str):
            filenames = [filename_val]
        else:
            print(
                f"Unexpected type for 'filename' in metadata: {type(filename_val)}. Expected str or list."
            )
            continue  # Skip this chunk

        # Add chunk to groups for each associated filename
        for fname in filenames:
            if not isinstance(fname, str):
                print(
                    f"Expected filename to be a string, but got {type(fname)} in list: {filenames}."
                )
                continue  # Skip this filename

            # Preserve the structure with the three main keys
            grouped_chunks[fname].append(
                {"idx": chunk.get("idx"), "text": text, "metadata": metadata}
            )

    print("📄 Documents found:", list(grouped_chunks.keys()))

    for filename in grouped_chunks:
        print(f"\n--- {filename} ---")
        print(f"Chunks: {len(grouped_chunks[filename])}")

    # Count words in each chunk
    all_chunks = [
        chunk["text"]
        for chunks_list in grouped_chunks.values()
        for chunk in chunks_list
    ]
    word_counts = [len(chunk.split()) for chunk in all_chunks]

    # Print summary
    for i, count in enumerate(word_counts):
        print(f"Chunk {i}: {count} words")

    # Ensure directory exists
    os.makedirs(os.path.dirname(GROUPED_CHUNKS_FILE), exist_ok=True)

    # Write to file
    with open(GROUPED_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(grouped_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Grouped chunks written to {GROUPED_CHUNKS_FILE}")

    return GROUPED_CHUNKS_FILE


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
            list1 = [val1] if not isinstance(val1, list) else val1
            list2 = [val2] if not isinstance(val2, list) else val2
            combined = list1 + list2
            # Simple types in special_keys are hashable, dict.fromkeys is fine
            merged[key] = list(dict.fromkeys(combined)) if combined else []
            # If only one item after deduplication and original wasn't a list, keep as single item
            if len(merged[key]) == 1 and not (
                isinstance(val1, list) or isinstance(val2, list)
            ):
                merged[key] = merged[key][0]
            elif not merged[key]:  # Handle empty case
                merged[key] = (
                    [] if (isinstance(val1, list) or isinstance(val2, list)) else None
                )

        elif key == "bounding_boxes" or key == "charspans":
            # For bounding boxes and charspans, we need to preserve their relationship
            # with pages, so we need to be careful when merging
            # Initialize page_mappings structure
            if "page_mappings" not in merged:
                merged["page_mappings"] = {}
            if not isinstance(merged["page_mappings"], dict):  # Ensure it's a dict
                merged["page_mappings"] = {}
            if f"{key}_page_map" not in merged["page_mappings"]:
                merged["page_mappings"][f"{key}_page_map"] = {}

            # Combine the lists (handle non-list cases)
            list1 = (
                val1 if isinstance(val1, list) else ([val1] if val1 is not None else [])
            )
            list2 = (
                val2 if isinstance(val2, list) else ([val2] if val2 is not None else [])
            )
            merged[key] = (
                list1 + list2
            )  # Keep duplicates for now, associate with page first

            # Map the elements to their pages
            pages1 = meta1.get("pages", [])
            if not isinstance(pages1, list):
                pages1 = [pages1] if pages1 is not None else []
            pages2 = meta2.get("pages", [])
            if not isinstance(pages2, list):
                pages2 = [pages2] if pages2 is not None else []

            current_page_map = merged["page_mappings"][f"{key}_page_map"]
            # Map items from meta1
            if pages1:
                for i, item in enumerate(list1):
                    page_idx = i % len(pages1) if len(pages1) > 0 else 0
                    page = pages1[page_idx]
                    # Use original index from list1 as key
                    current_page_map[str(i)] = page
            # Map items from meta2, offset index
            if pages2:
                for i, item in enumerate(list2):
                    page_idx = i % len(pages2) if len(pages2) > 0 else 0
                    page = pages2[page_idx]
                    # Use offset index from list2 as key
                    current_page_map[str(len(list1) + i)] = page

            # Note: Deduplication of bounding_boxes/charspans happens in finalise_chunks.py
            # based on page association. We keep duplicates here to maintain correct mapping.

        elif key == "page_mappings":
            # Special handling to merge page_mappings dictionaries correctly
            if isinstance(val1, dict) and isinstance(val2, dict):
                merged_page_map = {}
                map_keys = set(val1.keys()) | set(val2.keys())
                for map_key in map_keys:  # e.g., 'bounding_boxes_page_map'
                    map1 = val1.get(map_key, {})
                    map2 = val2.get(map_key, {})
                    if isinstance(map1, dict) and isinstance(map2, dict):
                        # Merge the inner index->page dictionaries
                        merged_page_map[map_key] = {**map1, **map2}
                    elif isinstance(map1, dict):
                        merged_page_map[map_key] = map1
                    else:
                        merged_page_map[map_key] = map2  # Keep map2 if map1 invalid
                merged[key] = merged_page_map
            elif isinstance(val1, dict):
                merged[key] = val1  # Keep the valid dict
            elif isinstance(val2, dict):
                merged[key] = val2  # Keep the valid dict
            else:
                merged[key] = {}  # Both invalid, initialize empty

        elif key == "headings":
            # For headings (assumed hashable), deduplicate while preserving order
            list1 = [val1] if not isinstance(val1, list) else val1
            list2 = [val2] if not isinstance(val2, list) else val2
            combined = list1 + list2
            merged[key] = list(
                dict.fromkeys(combined)
            )  # Use dict.fromkeys for ordered deduplication

        elif key == "document_summary" or key == "chunk_summary":
            # For document or chunk summaries, concatenate with a separator
            summary1 = val1 if val1 is not None else ""
            summary2 = val2 if val2 is not None else ""
            if summary1 and summary2:
                merged[key] = summary1 + " " + summary2
            else:
                merged[key] = summary1 or summary2

        else:  # Generic list handling
            list1 = (
                val1 if isinstance(val1, list) else ([val1] if val1 is not None else [])
            )
            list2 = (
                val2 if isinstance(val2, list) else ([val2] if val2 is not None else [])
            )
            combined = list1 + list2
            # Try to deduplicate if possible (for hashable elements)
            try:
                merged[key] = list(dict.fromkeys(combined))
            except TypeError:  # If elements are not hashable
                merged[key] = combined

    return merged


def merge_small_chunks(
    grouped_chunks_file=GROUPED_CHUNKS_FILE,
    min_words=200,
):
    """
    Merge small chunks to meet minimum word count and write results to file.

    Args:
        grouped_chunks_file: Path to the JSON file with grouped chunks.
        min_words: Minimum number of words per chunk.

    Returns:
        Path to the merged chunks file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(MERGED_CHUNKS_FILE), exist_ok=True)

    # Load grouped chunks from file
    with open(grouped_chunks_file, "r", encoding="utf-8") as f:
        grouped_chunks = json.load(f)

    merged_grouped_chunks = {}

    for filename in grouped_chunks:
        chunks_with_metadata = grouped_chunks[filename]

        merged = True
        while merged:
            merged = False
            new_chunks_with_metadata = []
            i = 0

            while i < len(chunks_with_metadata):
                current_chunk = chunks_with_metadata[i]
                text = current_chunk.get("text", "")
                word_count = count_words(text)

                if word_count >= min_words:
                    new_chunks_with_metadata.append(current_chunk)
                    i += 1
                else:
                    prev_len = (
                        count_words(chunks_with_metadata[i - 1].get("text", ""))
                        if i > 0
                        else float("inf")
                    )
                    next_len = (
                        count_words(chunks_with_metadata[i + 1].get("text", ""))
                        if i + 1 < len(chunks_with_metadata)
                        else float("inf")
                    )

                    if next_len <= prev_len and i + 1 < len(chunks_with_metadata):
                        # Merge with next
                        current_meta = current_chunk.get("metadata", {})
                        next_chunk = chunks_with_metadata[i + 1]
                        next_text = next_chunk.get("text", "")
                        next_meta = next_chunk.get("metadata", {})

                        # Merge metadata
                        merged_meta = merge_metadata(current_meta, next_meta)

                        # Create new merged chunk with combined text and maintaining structure
                        new_chunk = {
                            "idx": current_chunk.get("idx"),  # Keep original idx
                            "text": text + " " + next_text,
                            "metadata": merged_meta,
                        }

                        new_chunks_with_metadata.append(new_chunk)
                        i += 2
                        merged = True
                    elif i > 0:
                        # Merge with previous
                        prev_chunk = new_chunks_with_metadata[-1]
                        prev_text = prev_chunk.get("text", "")
                        prev_meta = prev_chunk.get("metadata", {})
                        current_meta = current_chunk.get("metadata", {})

                        # Merge metadata
                        merged_meta = merge_metadata(prev_meta, current_meta)

                        # Update previous chunk with merged data while maintaining structure
                        new_chunks_with_metadata[-1] = {
                            "idx": prev_chunk.get("idx"),  # Keep previous idx
                            "text": prev_text + " " + text,
                            "metadata": merged_meta,
                        }

                        i += 1
                        merged = True
                    else:
                        # Nowhere to merge
                        new_chunks_with_metadata.append(current_chunk)
                        i += 1

            chunks_with_metadata = new_chunks_with_metadata

        merged_grouped_chunks[filename] = chunks_with_metadata

    print("✅ Merging complete.")
    print(f"Documents processed: {len(merged_grouped_chunks)}")
    for filename, chunks in merged_grouped_chunks.items():
        print(f"\n📄 Document: {filename}")
        word_counts = [len(chunk.get("text", "").split()) for chunk in chunks]

        print(f"  ➤ Avg words: {sum(word_counts) / len(word_counts):.2f}")
        print(f"  ➤ Max words: {max(word_counts)}")
        print(f"  ➤ Min words: {min(word_counts)}")

    # Write merged chunks to file
    with open(MERGED_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_grouped_chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Merged chunks written to {MERGED_CHUNKS_FILE}")

    return MERGED_CHUNKS_FILE


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
        full_text = " ".join(chunk.get("text", "") for chunk in chunks)
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
