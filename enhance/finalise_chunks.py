import json
import os

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
ENHANCED_CHUNKS_FILE = ENV["ENHANCED_CHUNKS_FILE"]
ENHANCED_METADATA_FILE = ENV["ENHANCED_METADATA_FILE"]
SUMMARISE_CHUNK_FILE = ENV["SUMMARISE_CHUNK_OUTPUT_FILE"]
SUMMARISE_OUTPUT_FILE = ENV.get(
    "SUMMARISE_OUTPUT_FILE", "data/enhanced/document_summaries.json"
)
MERGED_CHUNKS_FILE = ENV.get("MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json")
MERGED_METADATA_FILE = ENV.get(
    "MERGED_METADATA_FILE", "data/enhanced/merged_metadata.json"
)


def export_enriched_chunks_and_metadata(
    doc_summaries_file=SUMMARISE_OUTPUT_FILE,  # Expecting JSON path
    chunk_context_summaries_file=SUMMARISE_CHUNK_FILE,  # Expecting JSON path
    merged_chunks_file=MERGED_CHUNKS_FILE,
    merged_metadata_file=MERGED_METADATA_FILE,
    output_chunks_file=ENHANCED_CHUNKS_FILE,
    output_metadata_file=ENHANCED_METADATA_FILE,
):
    """
    Load document-level summaries (JSON), chunk-level summaries (JSON), and chunk data,
    enrich the metadata, and export both merged chunks and enriched metadata to JSON.

    Args:
        doc_summaries_file (str): Path to JSON file for document-level summaries (filename -> summary).
        chunk_context_summaries_file (str): Path to JSON file for chunk-level summaries (filename -> list of summaries).
        merged_chunks_file (str): Path to JSON file containing merged chunks (filename -> list of chunks).
        merged_metadata_file (str): Path to JSON file containing merged metadata.
        output_chunks_file (str): Output path for enriched chunks (list of strings).
        output_metadata_file (str): Output path for enriched metadata (list of dicts).

    Returns:
        tuple: (output_chunks_file, output_metadata_file)
    """
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_chunks_file), exist_ok=True)
    os.makedirs(os.path.dirname(output_metadata_file), exist_ok=True)

    # --- Load merged chunks and metadata ---
    try:
        with open(merged_chunks_file, "r", encoding="utf-8") as f:
            merged_grouped_chunks = json.load(f)
        print(f"✅ Loaded merged chunks from {merged_chunks_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading merged chunks from {merged_chunks_file}: {e}")
        return None, None  # Cannot proceed without chunks

    try:
        with open(merged_metadata_file, "r", encoding="utf-8") as f:
            merged_grouped_metadata = json.load(f)
        print(f"✅ Loaded merged metadata from {merged_metadata_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading merged metadata from {merged_metadata_file}: {e}")
        return None, None  # Cannot proceed without metadata

    # --- Load chunk context summaries (directly from JSON) ---
    try:
        with open(chunk_context_summaries_file, "r", encoding="utf-8") as f:
            chunk_context_summaries = json.load(f)
        print(
            f"✅ Loaded chunk context summaries from JSON: {chunk_context_summaries_file}"
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(
            f"❌ Error loading chunk context summaries from {chunk_context_summaries_file}: {e}"
        )
        print("Proceeding without chunk context summaries.")
        chunk_context_summaries = {}

    # --- Load document summaries (directly from JSON) ---
    try:
        with open(doc_summaries_file, "r", encoding="utf-8") as f:
            doc_summaries = json.load(f)
        print(f"✅ Loaded document summaries from JSON: {doc_summaries_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading document summaries from {doc_summaries_file}: {e}")
        print("Proceeding without document summaries.")
        doc_summaries = {}

    # --- Prepare containers ---
    all_merged_chunks = []
    all_enriched_metadata = []

    # --- Loop through each document ---
    print("\n enriquecendo metadados...")  # Enriching metadata
    processed_files = 0
    skipped_files = 0
    for filename in merged_grouped_chunks:
        chunks = merged_grouped_chunks.get(filename, [])
        metadata_list = merged_grouped_metadata.get(filename, [])
        chunk_contexts = chunk_context_summaries.get(filename, [])
        doc_summary = doc_summaries.get(filename, "[ERROR: Summary not found]")

        # Basic validation
        if not chunks or not metadata_list:
            print(
                f"⚠️ Warning: Missing chunks or metadata for document '{filename}' — skipping."
            )
            skipped_files += 1
            continue

        if len(chunks) != len(metadata_list):
            print(
                f"⚠️ Warning: Chunk ({len(chunks)}) and metadata ({len(metadata_list)}) count mismatch in '{filename}' — skipping."
            )
            skipped_files += 1
            continue

        if len(chunks) != len(chunk_contexts):
            print(
                f"⚠️ Warning: Chunk ({len(chunks)}) and chunk summary ({len(chunk_contexts)}) count mismatch in '{filename}'. Padding summaries."
            )
            # Pad chunk_contexts if necessary
            chunk_contexts.extend(
                ["[ERROR: Summary missing]"] * (len(chunks) - len(chunk_contexts))
            )

        print(f"  Processing file: {filename} ({len(chunks)} chunks)")
        processed_files += 1
        for chunk_idx, (chunk, meta, chunk_summary) in enumerate(
            zip(chunks, metadata_list, chunk_contexts)
        ):
            # Store each chunk as an object with text and source information
            chunk_id = f"{filename}_{chunk_idx}"
            chunk_obj = {
                "text": chunk,
                "source_file": filename,
                "chunk_index": chunk_idx,
                "chunk_id": chunk_id,  # Unique identifier that matches the metadata
            }
            all_merged_chunks.append(chunk_obj)

            # Enrich metadata by adding summaries to the original metadata
            # This uses the doc_summary loaded for the file and the specific chunk_summary
            enriched_meta = {
                **meta,  # Spread the original metadata keys
                "document_summary": doc_summary,
                "chunk_context_summary": chunk_summary,
                "chunk_id": chunk_id,  # Same ID as in the chunks file for linking
                "source_file": filename,  # Explicitly add source file for easier querying
            }

            # Ensure essential keys from the original meta are present (even if None/empty)
            # This step might be redundant if meta is guaranteed to have them,
            # but acts as a safeguard.
            for key_to_ensure in [
                "filename",
                "id",
                "pages",
                "headings",
                "bounding_boxes",
                "charspans",
            ]:
                if key_to_ensure not in enriched_meta:
                    # Provide sensible defaults if missing from original meta
                    if key_to_ensure in ["pages", "headings"]:
                        enriched_meta[key_to_ensure] = []
                    elif key_to_ensure in ["bounding_boxes", "charspans"]:
                        enriched_meta[key_to_ensure] = {}
                    elif key_to_ensure == "id":
                        enriched_meta[key_to_ensure] = f"{filename}_chunk_{chunk_idx}"
                    else:
                        enriched_meta[key_to_ensure] = filename  # Default filename

            all_enriched_metadata.append(enriched_meta)

    # --- Write output files ---
    print(f"\nProcessed {processed_files} files, skipped {skipped_files} files.")
    print(f"Total enriched chunks: {len(all_merged_chunks)}")

    try:
        with open(output_chunks_file, "w", encoding="utf-8") as f:
            json.dump(all_merged_chunks, f, ensure_ascii=False, indent=2)
        print(f"✅ Enriched chunks written to {output_chunks_file}")
    except IOError as e:
        print(f"❌ Error writing chunks file {output_chunks_file}: {e}")
        return None, None

    try:
        with open(output_metadata_file, "w", encoding="utf-8") as f:
            json.dump(all_enriched_metadata, f, ensure_ascii=False, indent=2)
        print(f"✅ Enriched metadata written to {output_metadata_file}")
    except IOError as e:
        print(f"❌ Error writing metadata file {output_metadata_file}: {e}")
        return None, None

    print("\n✅ Export complete:")

    return output_chunks_file, output_metadata_file
