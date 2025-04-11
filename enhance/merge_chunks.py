from collections import defaultdict
from typing import Any, Dict, List, Tuple


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
    # Convert defaultdicts to regular dicts for the return value
    return dict(grouped_chunks), dict(grouped_metadata)


def to_list(x):
    return x if isinstance(x, list) else [x]


def merge_metadata(meta1, meta2):
    return {
        "id": to_list(meta1.get("id", [])) + to_list(meta2.get("id", [])),
        "headings": to_list(meta1.get("headings", []))
        + to_list(meta2.get("headings", [])),
        "filename": list(
            set(to_list(meta1.get("filename", [])) + to_list(meta2.get("filename", [])))
        ),
        "page_no": sorted(
            list(
                set(
                    to_list(meta1.get("page_no", []) or meta1.get("pages", []))
                    + to_list(meta2.get("page_no", []) or meta2.get("pages", []))
                )
            )
        ),
    }


def count_words(text):
    return len(text.split())


def merge_small_chunks(grouped_chunks, grouped_metadata, min_words=200):
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
    return merged_grouped_chunks, merged_grouped_metadata


def build_full_docs(merged_grouped_chunks):
    """
    Combines chunks of text per document into full document strings.

    Args:
        merged_grouped_chunks (dict): Mapping of filename to list of text chunks.

    Returns:
        tuple: (full_docs, doc_filenames)
    """
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

    return full_docs, doc_filenames
