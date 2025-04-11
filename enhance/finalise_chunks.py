import json

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
ENHANCED_CHUNKS_FILE = ENV["ENHANCED_CHUNKS_FILE"]
ENHANCED_METADATA_FILE = ENV["ENHANCED_METADATA_FILE"]
SUMMARISE_CHUNK_FILE = ENV["SUMMARISE_CHUNK_OUTPUT_FILE"]


def export_enriched_chunks_and_metadata(
    
    merged_grouped_chunks,
    merged_grouped_metadata,
    chunk_context_summaries,
    summaries_path=SUMMARISE_CHUNK_FILE,
    output_chunks_file="merged_chunks.json",
    output_metadata_file="merged_metadata_enriched.json",
):
    """
    Load document-level summaries, enrich chunk-level metadata, and export both merged chunks and enriched metadata.

    Args:
        summaries_path (str): Path to document-level summaries (plain text format).
        merged_grouped_chunks (dict): filename -> list of text chunks.
        merged_grouped_metadata (dict): filename -> list of metadata dicts.
        chunk_context_summaries (dict): filename -> list of chunk-level context summaries.
        output_chunks_file (str): Output path for merged chunks.
        output_metadata_file (str): Output path for enriched metadata.

    Returns:
        tuple: (all_merged_chunks, all_enriched_metadata)
    """
    # --- Load and parse the summaries ---
    doc_summaries = {}
    current_filename = None
    current_summary_lines = []

    with open(summaries_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.endswith(":") and not line.startswith(" "):
                # Save previous summary if any
                if current_filename and current_summary_lines:
                    doc_summaries[current_filename] = " ".join(
                        current_summary_lines
                    ).strip()
                    current_summary_lines = []
                current_filename = line[:-1]  # Remove the trailing colon
            elif current_filename:
                current_summary_lines.append(line)

        # Save last summary
        if current_filename and current_summary_lines:
            doc_summaries[current_filename] = " ".join(current_summary_lines).strip()

    print(f"✅ Loaded {len(doc_summaries)} document summaries.")

    # --- Prepare containers ---
    all_merged_chunks = []
    all_enriched_metadata = []

    # --- Loop through each document ---
    for filename in merged_grouped_chunks:
        chunks = merged_grouped_chunks[filename]
        metadata_list = merged_grouped_metadata[filename]
        chunk_contexts = chunk_context_summaries.get(filename, [])
        doc_summary = doc_summaries.get(filename, "[ERROR: Summary not found]")

        if len(chunks) != len(metadata_list) or len(chunks) != len(chunk_contexts):
            print(f"⚠️  Warning: Length mismatch in document '{filename}' — skipping.")
            continue  # Skip misaligned data

        for chunk, meta, chunk_summary in zip(chunks, metadata_list, chunk_contexts):
            all_merged_chunks.append(chunk)
            enriched_meta = {
                **meta,
                "document_summary": doc_summary,
                "chunk_context_summary": chunk_summary,
            }
            all_enriched_metadata.append(enriched_meta)

    # --- Write output files ---
    with open(output_chunks_file, "w", encoding="utf-8") as f:
        json.dump(all_merged_chunks, f, ensure_ascii=False, indent=2)

    with open(output_metadata_file, "w", encoding="utf-8") as f:
        json.dump(all_enriched_metadata, f, ensure_ascii=False, indent=2)

    print("\n✅ Export complete:")
    print(f"  - {output_chunks_file}")
    print(f"  - {output_metadata_file}")
    print(f"  ➤ Total merged chunks: {len(all_merged_chunks)}")

    return all_merged_chunks, all_enriched_metadata
