import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).absolute().parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.load_env import get_env_vars

# Load environment variables
ENV = get_env_vars()
CHUNKS_FILE = ENV.get("CHUNKS_FILE", "data/chunked/chunks.json")
METADATA_FILE = ENV.get("METADATA_FILE", "data/chunked/metadata.json")
EXTRACTED_CHUNKS_FILE = ENV.get(
    "EXTRACTED_CHUNKS_FILE", "data/chunked/extracted_chunks.json"
)


def convert_to_unified_format(
    chunks_file=CHUNKS_FILE,
    metadata_file=METADATA_FILE,
    output_file=EXTRACTED_CHUNKS_FILE,
):
    """
    Convert separate chunks and metadata files to a unified format.

    Args:
        chunks_file (str): Path to the chunks JSON file
        metadata_file (str): Path to the metadata JSON file
        output_file (str): Path to save the unified chunks to

    Returns:
        str: Path to the unified chunks file
    """
    print(
        f"Converting {chunks_file} and {metadata_file} to unified format at {output_file}"
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load chunks and metadata
    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"✅ Loaded {len(chunks)} chunks from {chunks_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading chunks from {chunks_file}: {e}")
        return None

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"✅ Loaded {len(metadata)} metadata entries from {metadata_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading metadata from {metadata_file}: {e}")
        return None

    # Validate chunks and metadata
    if len(chunks) != len(metadata):
        print(
            f"❌ Error: Mismatch between chunks ({len(chunks)}) and metadata ({len(metadata)})"
        )
        return None

    # Create unified chunks
    unified_chunks = []
    for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
        # Create a unified chunk with idx, text, and metadata structure
        unified_chunk = {
            "idx": i,
            "text": chunk,
            "metadata": {
                **meta,  # Include all original metadata
                "document_summary": "",  # Initialize empty document summary
                "chunk_summary": "",  # Initialize empty chunk summary
            },
        }
        unified_chunks.append(unified_chunk)

    # Write unified chunks to file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(unified_chunks, f, ensure_ascii=False, indent=2)
        print(f"✅ Wrote {len(unified_chunks)} unified chunks to {output_file}")
    except IOError as e:
        print(f"❌ Error writing unified chunks to {output_file}: {e}")
        return None

    return output_file


if __name__ == "__main__":
    convert_to_unified_format()
