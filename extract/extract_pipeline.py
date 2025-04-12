import argparse
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


def parse_args():
    """Parse command line arguments for the extraction pipeline."""
    parser = argparse.ArgumentParser(
        description="Extract, chunk, and process documents for RAG",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input-folder",
        type=str,
        default=str(INPUT_FOLDER),
        help="Directory containing input documents to process",
    )

    parser.add_argument(
        "--output-file",
        type=str,
        default=str(EXTRACTED_CHUNKS_FILE),
        help="Path to the JSON file where extracted chunks will be saved",
    )

    parser.add_argument(
        "--clear-output",
        action="store_true",
        help="Clear the output file before processing",
    )

    parser.add_argument(
        "--min-words",
        type=int,
        default=MIN_WORDS,
        help="Minimum number of words per chunk",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=MAX_TOKENS,
        help="Maximum number of tokens per chunk",
    )

    parser.add_argument(
        "--specific-file",
        type=str,
        default=None,
        help="Process only this specific file (full path)",
    )

    return parser.parse_args()


def process_single_document(
    input_doc_path,
    extracted_chunks_file=EXTRACTED_CHUNKS_FILE,
    min_words=MIN_WORDS,
    max_tokens=MAX_TOKENS,
):
    """
    Process a single document through the entire pipeline:
    1. Extract and chunk the document
    2. Merge small chunks
    3. Write to the unified chunks file

    Args:
        input_doc_path: Path to the input document
        extracted_chunks_file: Path to the output JSON file
        min_words: Minimum words per chunk
        max_tokens: Maximum tokens per chunk

    Returns:
        bool: True if processing was successful
    """
    print(f"\n🔍 Processing: {input_doc_path.name}")

    # Initialize chunker with tokenizer
    tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID)
    chunker = HybridChunker(
        tokenizer=tokenizer, max_tokens=max_tokens, merge_peers=True
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
        min_words = min_words

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
            f"  ✓ Merged into {len(merged_chunks)} chunks with minimum {min_words} words"
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
    args = parse_args()

    # Update parameters based on command line arguments
    input_folder = Path(args.input_folder)
    extracted_chunks_file = args.output_file
    min_words = args.min_words
    max_tokens = args.max_tokens

    print("\n" + "=" * 80)
    print("📚 DOCUMENT EXTRACTION PIPELINE")
    print("=" * 80 + "\n")

    print(f"  ➤ Input folder: {input_folder}")
    print(f"  ➤ Output file: {extracted_chunks_file}")
    print(f"  ➤ Min words per chunk: {min_words}")
    print(f"  ➤ Max tokens per chunk: {max_tokens}")

    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(extracted_chunks_file), exist_ok=True)

    # Clear the output file if specified
    if args.clear_output and os.path.exists(extracted_chunks_file):
        print(f"  ➤ Clearing output file: {extracted_chunks_file}")
        with open(extracted_chunks_file, "w") as f:
            f.write("[]")

    # Process a specific file if requested
    if args.specific_file:
        specific_file = Path(args.specific_file)
        if specific_file.exists():
            success = process_single_document(
                specific_file,
                extracted_chunks_file,
                min_words=min_words,
                max_tokens=max_tokens,
            )
            if success:
                print("\n✅ Successfully processed the specified file.")
            else:
                print("\n❌ Failed to process the specified file.")
            return
        else:
            print(f"❌ Specified file not found: {specific_file}")
            return

    # Check if the input folder exists
    if not input_folder.exists():
        print(f"❌ Input folder does not exist: {input_folder}")
        return

    # Process all PDF files in the input folder
    pdf_files = list(input_folder.glob("**/*.pdf"))
    print(f"  ➤ Found {len(pdf_files)} PDF files to process")

    successful = 0
    failed = 0

    for pdf_file in pdf_files:
        success = process_single_document(
            pdf_file, extracted_chunks_file, min_words=min_words, max_tokens=max_tokens
        )
        if success:
            successful += 1
        else:
            failed += 1

    print("\n" + "=" * 80)
    print(f"✅ Extraction completed: {successful} succeeded, {failed} failed")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
