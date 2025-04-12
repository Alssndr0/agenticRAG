import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import using relative imports for files in the same directory
from docling.chunking import HybridChunker
from extract_chunk_metadata import extract_all_chunks_metadata
from transformers import AutoTokenizer
from write_chunks import write_unified_chunks

from extract import convert_pdf_with_vlm
from utils.load_env import get_env_vars

env_vars = get_env_vars(force_reload=True)
INPUT_FOLDER = Path(env_vars["INPUT_FOLDER"])
OUTPUT_FOLDER = Path(env_vars["OUTPUT_FOLDER"])
MAX_TOKENS = int(env_vars["CHUNK_SIZE"])
EMBED_MODEL_ID = env_vars["EMBED_MODEL_ID"]
EXTRACTED_CHUNKS_FILE = env_vars["EXTRACTED_CHUNKS_FILE"]
MIN_WORDS = int(env_vars.get("MIN_WORDS", "200"))  # Minimum words per chunk


def process_single_document(
    input_doc_path, extracted_chunks_file=EXTRACTED_CHUNKS_FILE
):
    """
    Process a single document through the entire pipeline:
    1. Extract and chunk the document
    2. Merge small chunks
    3. Write to the unified chunks file

    Args:
        input_doc_path: Path to the input document
        extracted_chunks_file: Path to the output JSON file

    Returns:
        bool: True if processing was successful
    """
    print(f"\n🔍 Processing: {input_doc_path.name}")

    # Initialize chunker with tokenizer
    tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID)
    chunker = HybridChunker(
        tokenizer=tokenizer, max_tokens=MAX_TOKENS, merge_peers=True
    )

    try:
        # Convert the document
        extraction = convert_pdf_with_vlm(input_doc_path)

        # Chunk the document
        document_chunks = list(chunker.chunk(dl_doc=extraction.document))
        print(f"  ✓ Created {len(document_chunks)} initial chunks")

        # Process and extract metadata from chunks
        processed_chunks = extract_all_chunks_metadata(document_chunks)
        print(f"  ✓ Extracted metadata for {len(processed_chunks)} chunks")

        # Merge small chunks to meet minimum size requirements
        # Instead of passing processed_chunks directly, we need to group them by filename first
        # and create a dictionary structure that merge_small_chunks expects
        grouped_chunks = {}
        for chunk in processed_chunks:
            filename = chunk.get("metadata", {}).get("filename", [])
            if not filename:
                continue

            # Handle both list and string cases for filename
            if isinstance(filename, list):
                if not filename:  # Skip if empty list
                    continue
                filename = filename[0]  # Use the first filename in the list

            # Initialize empty list for this filename if needed
            if filename not in grouped_chunks:
                grouped_chunks[filename] = []

            # Add chunk to appropriate group
            grouped_chunks[filename].append(chunk)

        # Now perform the merge on the grouped structure
        merged_grouped_chunks = {}
        min_words = MIN_WORDS

        for filename, chunks_with_metadata in grouped_chunks.items():
            merged = True
            while merged:
                merged = False
                new_chunks_with_metadata = []
                i = 0

                while i < len(chunks_with_metadata):
                    current_chunk = chunks_with_metadata[i]
                    text = current_chunk.get("text", "")
                    word_count = len(text.split())

                    if word_count >= min_words:
                        new_chunks_with_metadata.append(current_chunk)
                        i += 1
                    else:
                        prev_len = (
                            len(chunks_with_metadata[i - 1].get("text", "").split())
                            if i > 0
                            else float("inf")
                        )
                        next_len = (
                            len(chunks_with_metadata[i + 1].get("text", "").split())
                            if i + 1 < len(chunks_with_metadata)
                            else float("inf")
                        )

                        if next_len <= prev_len and i + 1 < len(chunks_with_metadata):
                            # Merge with next
                            from merge_chunks import merge_metadata

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
                            from merge_chunks import merge_metadata

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

        # Flatten the merged chunks back to a list for further processing
        merged_chunks = []
        for filename, chunks in merged_grouped_chunks.items():
            merged_chunks.extend(chunks)

        print(
            f"  ✓ Merged into {len(merged_chunks)} chunks with minimum {MIN_WORDS} words"
        )

        # Print statistics
        word_counts = [len(chunk.get("text", "").split()) for chunk in merged_chunks]
        if word_counts:
            print(f"  ➤ Avg words per chunk: {sum(word_counts) / len(word_counts):.2f}")
            print(f"  ➤ Max words per chunk: {max(word_counts)}")
            print(f"  ➤ Min words per chunk: {min(word_counts)}")

        # Write merged chunks to unified file
        write_unified_chunks(merged_chunks, extracted_chunks_file, append=True)
        print(f"  ✓ Wrote {len(merged_chunks)} chunks to {extracted_chunks_file}")

        return True
    except Exception as e:
        print(f"❌ Error processing {input_doc_path.name}: {str(e)}")
        return False


def main():
    """Run the extraction pipeline for all files in the input folder."""
    print("\n🚀 Starting document extraction pipeline")
    print(f"  ➤ Input folder: {INPUT_FOLDER}")
    print(f"  ➤ Output file: {EXTRACTED_CHUNKS_FILE}")
    print(f"  ➤ Min words per chunk: {MIN_WORDS}")

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(EXTRACTED_CHUNKS_FILE), exist_ok=True)

    # Process each PDF document one at a time
    successful_files = 0
    failed_files = 0

    for input_doc_path in sorted(INPUT_FOLDER.glob("*.pdf")):
        if process_single_document(input_doc_path, EXTRACTED_CHUNKS_FILE):
            successful_files += 1
        else:
            failed_files += 1

    print("\n✅ Extraction pipeline complete!")
    print(f"  ➤ Successfully processed: {successful_files} files")
    if failed_files > 0:
        print(f"  ➤ Failed to process: {failed_files} files")


if __name__ == "__main__":
    main()
