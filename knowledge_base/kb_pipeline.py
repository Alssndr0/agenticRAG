#!/usr/bin/env python3
"""
Knowledge Base Pipeline

This script processes enhanced chunks from JSON and creates both vector (FAISS)
and sparse (BM25) indexes for retrieval.

Usage:
    python kb_pipeline.py --input data/enhanced/enhanced_chunks.json
    python kb_pipeline.py --input data/enhanced/enhanced_chunks.json --index-name custom_index_name
    python kb_pipeline.py --input data/enhanced/enhanced_chunks.json --create-faiss --no-bm25
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add the parent directory to sys.path to allow importing from knowledge_base
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_base.kb_builder import KbBuilder
from knowledge_base.load_embeddings import load_embedding_model
from knowledge_base.text_assembler import process_enhanced_chunks


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process enhanced chunks and create knowledge base indexes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--input",
        type=str,
        default="data/enhanced/enhanced_chunks.json",
        help="Path to enhanced chunks JSON file",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="indexes",
        help="Directory to store created indexes",
    )

    parser.add_argument(
        "--index-name",
        type=str,
        default="enhanced_chunks",
        help="Base name for the created index",
    )

    # Index type options
    index_group = parser.add_argument_group("Index types")
    index_group.add_argument(
        "--create-faiss",
        action="store_true",
        dest="create_faiss",
        help="Create FAISS vector index",
    )

    index_group.add_argument(
        "--no-faiss",
        action="store_false",
        dest="create_faiss",
        help="Skip FAISS vector index creation",
    )

    index_group.add_argument(
        "--create-bm25",
        action="store_true",
        dest="create_bm25",
        help="Create BM25 sparse index",
    )

    index_group.add_argument(
        "--no-bm25",
        action="store_false",
        dest="create_bm25",
        help="Skip BM25 sparse index creation",
    )

    # Set defaults
    parser.set_defaults(create_faiss=True, create_bm25=True)

    return parser.parse_args()


def load_enhanced_chunks(file_path: str) -> List[Dict[str, Any]]:
    """
    Load enhanced chunks from a JSON file.

    Args:
        file_path: Path to the enhanced chunks JSON file

    Returns:
        List of enhanced chunks
    """
    try:
        with open(file_path, "r") as f:
            chunks = json.load(f)

        if not isinstance(chunks, list):
            raise ValueError(f"Expected a list of chunks, got {type(chunks)}")

        if not chunks:
            print(f"Warning: No chunks found in {file_path}")

        return chunks
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to parse JSON file {file_path}: {e}")
    except Exception as e:
        raise RuntimeError(f"Error loading chunks from {file_path}: {e}")


def create_indexes(
    chunks: List[Dict[str, Any]],
    index_name: str,
    output_dir: str,
    create_faiss: bool = True,
    create_bm25: bool = True,
) -> bool:
    """
    Create vector and/or sparse indexes based on the processed chunks.

    Args:
        chunks: List of enhanced chunks
        index_name: Base name for the created index
        output_dir: Directory to store indexes
        create_faiss: Whether to create FAISS index
        create_bm25: Whether to create BM25 index

    Returns:
        True if indexes were created successfully, False otherwise
    """
    try:
        start_time = time.time()

        print("⏳ Loading embedding model...")
        model = load_embedding_model()

        print("⏳ Initializing KB builder...")
        kb_builder = KbBuilder(model)

        print(f"⏳ Processing {len(chunks)} chunks for embedding...")
        processed_chunks = process_enhanced_chunks(chunks)
        print(f"✅ Processed {len(processed_chunks)} chunks successfully")

        faiss_dir = os.path.join(output_dir, "FAISS-TEST")
        bm25_dir = os.path.join(output_dir, "bm25")

        # Create indexes as requested
        if create_faiss:
            print(
                f"⏳ Creating FAISS vector index with {len(processed_chunks)} chunks..."
            )
            os.makedirs(faiss_dir, exist_ok=True)
            kb_builder.create_save_faiss_index(processed_chunks, index_name)
            print(f"✅ FAISS index created successfully @ {faiss_dir}")

        if create_bm25:
            print(
                f"⏳ Creating BM25 sparse index with {len(processed_chunks)} chunks..."
            )
            os.makedirs(bm25_dir, exist_ok=True)
            kb_builder.create_save_bm25_index(processed_chunks, bm25_dir)
            print(f"✅ BM25 index created successfully @ {bm25_dir}")

        elapsed_time = time.time() - start_time
        print(f"🎉 All indexes created successfully in {elapsed_time:.2f} seconds!")
        return True

    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        import traceback

        traceback.print_exc()
        return False


def main() -> int:
    """
    Main entry point for the KB pipeline.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        print("\n" + "=" * 80)
        print("📚 KNOWLEDGE BASE PIPELINE")
        print("=" * 80 + "\n")

        args = parse_args()

        # Ensure the input file exists
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ Error: Input file not found: {input_path}")
            return 1

        # Create output directories
        os.makedirs(args.output_dir, exist_ok=True)

        print(f"📂 Loading enhanced chunks from {input_path}...")
        chunks = load_enhanced_chunks(input_path)
        print(f"✅ Loaded {len(chunks)} chunks")

        # Create indexes
        success = create_indexes(
            chunks,
            args.index_name,
            args.output_dir,
            args.create_faiss,
            args.create_bm25,
        )

        if success:
            print("\n" + "=" * 80)
            print("✅ KNOWLEDGE BASE PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 80 + "\n")
            return 0
        else:
            print("\n" + "=" * 80)
            print("❌ KNOWLEDGE BASE PIPELINE FAILED")
            print("=" * 80 + "\n")
            return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
