import json
import os

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
ENHANCED_CHUNKS_FILE = ENV["ENHANCED_CHUNKS_FILE"]
ENHANCED_METADATA_FILE = ENV["ENHANCED_METADATA_FILE"]
SUMMARISE_CHUNK_FILE = ENV["SUMMARISE_CHUNK_OUTPUT_FILE"]
SUMMARISE_OUTPUT_FILE = ENV.get(
    "SUMMARISE_OUTPUT_FILE", "data/enhanced/document_summaries.txt"
)
MERGED_CHUNKS_FILE = ENV.get("MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json")
MERGED_METADATA_FILE = ENV.get(
    "MERGED_METADATA_FILE", "data/enhanced/merged_metadata.json"
)


def export_enriched_chunks_and_metadata(
    doc_summaries_file=SUMMARISE_OUTPUT_FILE,
    chunk_context_summaries_file=SUMMARISE_CHUNK_FILE,
    merged_chunks_file=MERGED_CHUNKS_FILE,
    merged_metadata_file=MERGED_METADATA_FILE,
    output_chunks_file=ENHANCED_CHUNKS_FILE,
    output_metadata_file=ENHANCED_METADATA_FILE,
):
    """
    Load document-level summaries, chunk-level summaries, and chunk data from files,
    enrich the metadata, and export both merged chunks and enriched metadata.

    Args:
        doc_summaries_file (str): Path to document-level summaries (plain text format).
        chunk_context_summaries_file (str): Path to chunk-level summaries (plain text or JSON).
        merged_chunks_file (str): Path to JSON file containing merged chunks.
        merged_metadata_file (str): Path to JSON file containing merged metadata.
        output_chunks_file (str): Output path for enriched chunks.
        output_metadata_file (str): Output path for enriched metadata.

    Returns:
        tuple: (output_chunks_file, output_metadata_file)
    """
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_chunks_file), exist_ok=True)
    os.makedirs(os.path.dirname(output_metadata_file), exist_ok=True)

    # --- Load merged chunks and metadata ---
    with open(merged_chunks_file, "r", encoding="utf-8") as f:
        merged_grouped_chunks = json.load(f)

    with open(merged_metadata_file, "r", encoding="utf-8") as f:
        merged_grouped_metadata = json.load(f)

    # --- Load and parse chunk context summaries ---
    # First check if a JSON version exists
    json_summaries_file = chunk_context_summaries_file.replace(".txt", ".json")
    if os.path.exists(json_summaries_file):
        # Use the JSON version if available
        with open(json_summaries_file, "r", encoding="utf-8") as f:
            chunk_context_summaries = json.load(f)
        print(f"✅ Loaded chunk context summaries from JSON: {json_summaries_file}")
    else:
        # Otherwise parse the text file
        chunk_context_summaries = {}
        current_filename = None
        current_chunk_index = None
        current_chunk_lines = []

        with open(chunk_context_summaries_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("📄 Document:"):
                    # New document
                    current_filename = line.replace("📄 Document:", "").strip()
                    chunk_context_summaries[current_filename] = []
                elif line.startswith("Chunk ") and ":" in line:
                    # Save previous chunk if any
                    if (
                        current_filename
                        and current_chunk_index is not None
                        and current_chunk_lines
                    ):
                        summary = " ".join(current_chunk_lines).strip()
                        while (
                            len(chunk_context_summaries[current_filename])
                            <= current_chunk_index
                        ):
                            chunk_context_summaries[current_filename].append("")
                        chunk_context_summaries[current_filename][
                            current_chunk_index
                        ] = summary

                    # Start new chunk
                    parts = line.split(":")
                    current_chunk_index = int(parts[0].replace("Chunk", "").strip())
                    current_chunk_lines = [parts[1].strip()] if len(parts) > 1 else []
                elif current_filename and current_chunk_index is not None:
                    current_chunk_lines.append(line)

            # Save the last chunk
            if (
                current_filename
                and current_chunk_index is not None
                and current_chunk_lines
            ):
                summary = " ".join(current_chunk_lines).strip()
                while (
                    len(chunk_context_summaries[current_filename])
                    <= current_chunk_index
                ):
                    chunk_context_summaries[current_filename].append("")
                chunk_context_summaries[current_filename][current_chunk_index] = summary

        print(f"✅ Parsed chunk context summaries from: {chunk_context_summaries_file}")

    # --- Load and parse document summaries ---
    doc_summaries = {}
    current_filename = None
    current_summary_lines = []

    with open(doc_summaries_file, "r", encoding="utf-8") as f:
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

    print(
        f"✅ Loaded {len(doc_summaries)} document summaries from: {doc_summaries_file}"
    )

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
    print(f"  ➤ Total enriched chunks: {len(all_merged_chunks)}")

    return output_chunks_file, output_metadata_file
