import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from enhance.summarise_chunks import summarise_chunk_contexts
from enhance.summarise_docs import summarise_documents
from utils.load_env import get_env_vars

# Load environment variables
ENV = get_env_vars()

# Input/output file paths
EXTRACTED_CHUNKS_FILE = ENV.get(
    "EXTRACTED_CHUNKS_FILE", "data/chunked/extracted_chunks.json"
)
ENHANCED_CHUNKS_FILE = ENV.get(
    "ENHANCED_CHUNKS_FILE", "data/enhanced/enhanced_chunks.json"
)


def parse_args():
    """Parse command line arguments for the enhancement pipeline."""
    parser = argparse.ArgumentParser(
        description="Enhance extracted chunks with document and chunk summaries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input-file",
        type=str,
        default=EXTRACTED_CHUNKS_FILE,
        help="Path to the extracted chunks JSON file",
    )

    parser.add_argument(
        "--output-file",
        type=str,
        default=ENHANCED_CHUNKS_FILE,
        help="Path to save the enhanced chunks JSON file",
    )

    parser.add_argument(
        "--temp-dir",
        type=str,
        default="data/enhanced",
        help="Directory for temporary files during processing",
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files after processing",
    )

    return parser.parse_args()


def run_pipeline(
    input_file=EXTRACTED_CHUNKS_FILE,
    output_file=ENHANCED_CHUNKS_FILE,
    temp_dir="data/enhanced",
    keep_temp=False,
):
    """
    Run the enhance pipeline to enrich chunks with document and chunk summaries.
    The pipeline:
    1. Loads extracted chunks
    2. Groups them by filename
    3. Generates document summaries
    4. Generates chunk summaries
    5. Adds summaries to chunk metadata
    6. Saves enhanced chunks

    Args:
        input_file: Path to the extracted chunks JSON file
        output_file: Path to save the enhanced chunks JSON file
        temp_dir: Directory for temporary files during processing
        keep_temp: Whether to keep temporary files after processing

    Returns:
        bool: True if enhancement was successful, False otherwise
    """
    print("\n" + "=" * 80)
    print("✨ ENHANCE PIPELINE")
    print("=" * 80 + "\n")

    # Ensure the extracted chunks file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: Extracted chunks file {input_file} not found.")
        return False

    # Load the extracted chunks
    print(f"\n📄 Loading extracted chunks from {input_file}...")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"  ✅ Loaded {len(chunks)} chunks")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error: Failed to load chunks from {input_file}: {e}")
        return False

    # Group chunks by filename
    print("\n📑 Grouping chunks by filename...")
    chunks_by_filename = defaultdict(list)
    filenames = set()

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        filename = metadata.get("filename")

        # Handle both string and list cases for filename
        if isinstance(filename, list) and filename:
            filename = filename[0]  # Use the first filename if it's a list

        if filename:
            chunks_by_filename[filename].append(chunk)
            filenames.add(filename)

    print(f"  ✅ Found {len(filenames)} unique document files")

    # Extract full document texts for summarization
    print("\n📚 Preparing documents for summarization...")
    doc_filenames = list(filenames)
    full_docs = []

    for filename in doc_filenames:
        file_chunks = chunks_by_filename[filename]
        # Sort chunks by their idx if available
        file_chunks.sort(key=lambda x: x.get("idx", 0))
        # Combine all text from chunks into one document
        full_doc = " ".join(chunk.get("text", "") for chunk in file_chunks)
        full_docs.append(full_doc)

    # Create temporary files for the summarization process
    os.makedirs(temp_dir, exist_ok=True)

    # Save document filenames and full docs to temporary files
    doc_filenames_file = os.path.join(temp_dir, "temp_doc_filenames.json")
    full_docs_file = os.path.join(temp_dir, "temp_full_docs.json")

    with open(doc_filenames_file, "w", encoding="utf-8") as f:
        json.dump(doc_filenames, f, ensure_ascii=False)

    with open(full_docs_file, "w", encoding="utf-8") as f:
        json.dump(full_docs, f, ensure_ascii=False)

    # Generate document summaries
    print("\n📝 Generating document summaries...")
    doc_summaries_file = summarise_documents(
        doc_filenames_file=doc_filenames_file, full_docs_file=full_docs_file
    )

    # Load document summaries
    with open(doc_summaries_file, "r", encoding="utf-8") as f:
        doc_summaries = json.load(f)
    print(f"  ✅ Generated summaries for {len(doc_summaries)} documents")

    # Prepare data for chunk summarization
    # Convert chunks_by_filename to format expected by summarise_chunk_contexts
    # (text strings, not full chunk objects)
    merged_chunks_by_filename = {}
    for filename, file_chunks in chunks_by_filename.items():
        # Sort chunks by their idx
        file_chunks.sort(key=lambda x: x.get("idx", 0))
        # Extract just the text content
        merged_chunks_by_filename[filename] = [
            chunk.get("text", "") for chunk in file_chunks
        ]

    # Save merged chunks to a temporary file
    merged_chunks_file = os.path.join(temp_dir, "temp_merged_chunks.json")
    with open(merged_chunks_file, "w", encoding="utf-8") as f:
        json.dump(merged_chunks_by_filename, f, ensure_ascii=False)

    # Generate chunk summaries
    print("\n🔍 Generating chunk-level summaries...")
    chunk_summaries_file = summarise_chunk_contexts(
        doc_filenames_file=doc_filenames_file,
        summaries_file=doc_summaries_file,
        merged_chunks_file=merged_chunks_file,
    )

    # Load chunk summaries
    with open(chunk_summaries_file, "r", encoding="utf-8") as f:
        chunk_summaries_by_filename = json.load(f)

    total_chunk_summaries = sum(
        len(summaries) for summaries in chunk_summaries_by_filename.values()
    )
    print(f"  ✅ Generated {total_chunk_summaries} chunk summaries")

    # Add summaries to chunk metadata
    print("\n✨ Adding summaries to chunk metadata...")
    enhanced_chunks = []

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        filename = metadata.get("filename")

        # Handle both string and list cases for filename
        if isinstance(filename, list) and filename:
            filename = filename[0]  # Use the first filename in the list

        if filename:
            # Add document summary
            doc_summary = doc_summaries.get(filename, "")
            metadata["document_summary"] = doc_summary

            # Add chunk summary if available
            if filename in chunk_summaries_by_filename:
                # Find the corresponding chunk summary based on idx
                idx = chunk.get("idx", -1)
                # If idx is within the range of available summaries, use it
                if 0 <= idx < len(chunk_summaries_by_filename[filename]):
                    metadata["chunk_summary"] = chunk_summaries_by_filename[filename][
                        idx
                    ]
                else:
                    metadata["chunk_summary"] = ""
            else:
                metadata["chunk_summary"] = ""

        # Create enhanced chunk with updated metadata
        enhanced_chunk = {
            "idx": chunk.get("idx", 0),
            "text": chunk.get("text", ""),
            "metadata": metadata,
        }

        enhanced_chunks.append(enhanced_chunk)

    # Save enhanced chunks
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enhanced_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Enhanced chunks written to {output_file}")

    # Clean up temporary files
    if not keep_temp:
        try:
            os.remove(doc_filenames_file)
            os.remove(full_docs_file)
            os.remove(merged_chunks_file)
            print("  ✅ Temporary files cleaned up")
        except Exception as e:
            print(f"  ⚠️ Warning: Could not remove temporary files: {e}")
    else:
        print("  ℹ️ Temporary files kept as requested")

    print("\n" + "=" * 80)
    print("✅ ENHANCE PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80 + "\n")

    return True


def main():
    """Run the enhance pipeline with command line arguments."""
    args = parse_args()

    success = run_pipeline(
        input_file=args.input_file,
        output_file=args.output_file,
        temp_dir=args.temp_dir,
        keep_temp=args.keep_temp,
    )

    if not success:
        print("\n" + "=" * 80)
        print("❌ ENHANCE PIPELINE FAILED")
        print("=" * 80 + "\n")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
