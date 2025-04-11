import json
import os
from collections import defaultdict

from openai import OpenAI

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
SUMMARISE_OUTPUT_FILE = ENV["SUMMARISE_OUTPUT_FILE"]
SUMMARISE_MODEL = ENV["SUMMARISE_MODEL"]
SUMMARISE_DOCUMENT_INPUT_WORDS = ENV["SUMMARISE_DOCUMENT_INPUT_WORDS"]
SUMMARISE_DOCUMENT_PROMPT = ENV["SUMMARISE_DOCUMENT_PROMPT"]
SUMMARISE_CHUNK_PROMPT = ENV["SUMMARISE_CHUNK_PROMPT"]
SUMMARISE_CHUNK_OUTPUT_FILE = ENV["SUMMARISE_CHUNK_OUTPUT_FILE"]
DOC_FILENAMES_FILE = ENV.get("DOC_FILENAMES_FILE", "data/enhance/doc_filenames.json")
MERGED_CHUNKS_FILE = ENV.get("MERGED_CHUNKS_FILE", "data/enhance/merged_chunks.json")


def summarise_chunk_contexts(
    doc_filenames_file=DOC_FILENAMES_FILE,
    summaries_file=SUMMARISE_OUTPUT_FILE,
    merged_chunks_file=MERGED_CHUNKS_FILE,
    output_file=SUMMARISE_CHUNK_OUTPUT_FILE,
    model=SUMMARISE_MODEL,
    max_words=500,
    system_instruction="Provide only a very short, succinct context summary for the target text to improve its searchability. Start with 'This chunk details...'",
):
    """
    Generate chunk-level context summaries with a summary and surrounding context.

    Args:
        doc_filenames_file (str): Path to JSON file containing document filenames.
        summaries_file (str): Path to file containing document summaries.
        merged_chunks_file (str): Path to JSON file containing merged chunks.
        output_file (str): Output file path for saving summaries.
        model (str): LLM model name.
        max_words (int): Max words allowed per chunk/summary section.
        system_instruction (str): System prompt to guide the summarization.

    Returns:
        str: Path to the output file containing chunk summaries.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load document filenames
    with open(doc_filenames_file, "r", encoding="utf-8") as f:
        doc_filenames = json.load(f)

    # Load document summaries
    doc_summaries = {}
    current_filename = None
    current_summary_lines = []

    with open(summaries_file, "r", encoding="utf-8") as f:
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

    # Load merged chunks
    with open(merged_chunks_file, "r", encoding="utf-8") as f:
        merged_grouped_chunks = json.load(f)

    chunk_context_summaries = defaultdict(list)

    prompt_template = (
        "--Document Summary--\n{summary}\n"
        "-- Chunk before--\n{chunk_before}\n"
        "-- Target Chunk--\n{target_chunk}\n"
        "-- Chunk after--\n{chunk_after}"
    )

    def truncate(text, max_w):
        return " ".join(text.split()[:max_w])

    # Open the output file for writing as we go
    with open(output_file, "w", encoding="utf-8") as f_out:
        for filename in doc_filenames:
            summary = doc_summaries.get(filename, "[No summary available]")
            chunks = merged_grouped_chunks.get(filename, [])

            if not chunks:
                print(f"⚠️ Warning: No chunks found for {filename}")
                continue

            print(f"\n📄 Processing chunks for: {filename} ({len(chunks)} chunks)")
            f_out.write(f"\n📄 Document: {filename}\n")

            for i in range(len(chunks)):
                chunk_before = chunks[i - 1] if i > 0 else ""
                target_chunk = chunks[i]
                chunk_after = chunks[i + 1] if i < len(chunks) - 1 else ""

                prompt = prompt_template.format(
                    summary=truncate(summary, max_words),
                    chunk_before=truncate(chunk_before, max_words),
                    target_chunk=truncate(target_chunk, max_words),
                    chunk_after=truncate(chunk_after, max_words),
                )

                try:
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt},
                        ],
                    )

                    result = response.choices[0].message.content.strip()
                    chunk_context_summaries[filename].append(result)

                    print(f"  ✅ Chunk {i}: {result}")
                    # Write to file immediately
                    f_out.write(f"\nChunk {i}:\n{result}\n")
                    # Flush to ensure data is written even if an error occurs later
                    f_out.flush()

                except Exception as e:
                    error_msg = f"[ERROR: {str(e)}]"
                    print(f"  ❌ Error on chunk {i} in {filename}: {str(e)}")
                    chunk_context_summaries[filename].append(error_msg)
                    f_out.write(f"\nChunk {i}:\n{error_msg}\n")
                    f_out.flush()

    print(f"\n✅ All chunk-level context summaries written to '{output_file}'")

    # Also write the complete dictionary to a JSON file for easier programmatic access
    chunk_summaries_json = output_file.replace(".txt", ".json")
    with open(chunk_summaries_json, "w", encoding="utf-8") as f:
        json.dump(dict(chunk_context_summaries), f, ensure_ascii=False, indent=2)

    print(f"✅ JSON version of chunk summaries written to '{chunk_summaries_json}'")

    return output_file
