"""
Test script for the knowledge base pipeline components.
"""

import json
import os
import sys
from pprint import pprint

# Add the parent directory to sys.path to allow importing from knowledge_base
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_base.text_assembler import (
    assemble_text_for_embedding,
    process_enhanced_chunks,
)


def test_text_assembler():
    """Test the text assembly function with a sample chunk."""
    # Sample chunk from enhanced_chunks.json
    sample_chunk = {
        "idx": 0,
        "text": "This is a sample document text.",
        "metadata": {
            "document_summary": "This is a document summary.",
            "chunk_summary": "This is a chunk context summary.",
            "filename": ["sample.pdf"],
            "pages": [1, 2],
        },
    }

    # Process the sample chunk
    result = assemble_text_for_embedding(sample_chunk)

    # Print the result
    print("Assembled text:")
    print("=" * 50)
    print(result["chunk"])
    print("=" * 50)
    print("\nMetadata:")
    pprint(result["metadata"])

    # Verify the structure
    assert "Document Summary" in result["chunk"]
    assert "Document Context Summary" in result["chunk"]
    assert "Retrieved Document" in result["chunk"]
    assert result["metadata"] == sample_chunk["metadata"]

    print("\nTest passed!")


def test_with_real_data(file_path="data/enhanced/enhanced_chunks.json", limit=1):
    """Test the text assembly with real data from enhanced_chunks.json."""
    try:
        # Load sample data from the actual JSON file
        with open(file_path, "r") as f:
            chunks = json.load(f)

        if not chunks:
            print(f"No chunks found in {file_path}")
            return

        # Process a limited number of chunks
        print(f"Processing {min(limit, len(chunks))} chunks from {file_path}")
        processed = process_enhanced_chunks(chunks[:limit])

        # Print the first processed chunk
        if processed:
            print("\nSample processed chunk:")
            print("=" * 50)
            print(
                processed[0]["chunk"][:500] + "..."
                if len(processed[0]["chunk"]) > 500
                else processed[0]["chunk"]
            )
            print("=" * 50)
            print("\nProcessed chunks look good!")

    except Exception as e:
        print(f"Error testing with real data: {e}")


if __name__ == "__main__":
    print("Testing text assembler with sample data...")
    test_text_assembler()

    print("\nTesting with real data from enhanced_chunks.json...")
    test_with_real_data()
