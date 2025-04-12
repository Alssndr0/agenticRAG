import json
import os
from collections import defaultdict

from openai import OpenAI

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
SUMMARISE_OUTPUT_FILE = ENV.get(
    "SUMMARISE_OUTPUT_FILE", "data/enhanced/doc_summaries.json"
)
SUMMARISE_MODEL = ENV.get("SUMMARISE_MODEL", "gpt-4o")
SUMMARISE_DOCUMENT_INPUT_WORDS = ENV.get("SUMMARISE_DOCUMENT_INPUT_WORDS", "5000")
SUMMARISE_DOCUMENT_PROMPT = ENV.get(
    "SUMMARISE_DOCUMENT_PROMPT",
    "Provide a concise summary of the document in 2-3 sentences.",
)
SUMMARISE_CHUNK_PROMPT = ENV.get(
    "SUMMARISE_CHUNK_PROMPT", "Provide a concise summary of the chunk in 1-2 sentences."
)
SUMMARISE_CHUNK_OUTPUT_FILE = ENV.get(
    "SUMMARISE_CHUNK_OUTPUT_FILE", "data/enhanced/chunk_summaries.json"
)
DOC_FILENAMES_FILE = ENV.get("DOC_FILENAMES_FILE", "data/enhanced/doc_filenames.json")
MERGED_CHUNKS_FILE = ENV.get("MERGED_CHUNKS_FILE", "data/enhanced/merged_chunks.json")


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
    Generate chunk-level context summaries using document summaries and surrounding chunks,
    and write them to a JSON file.

    Args:
        doc_filenames_file (str): Path to JSON file containing document filenames.
        summaries_file (str): Path to JSON file containing document summaries (filename -> summary).
        merged_chunks_file (str): Path to JSON file containing merged chunks (filename -> list of chunks).
        output_file (str): JSON file path for saving chunk summaries (filename -> list of summaries).
        model (str): LLM model name.
        max_words (int): Max words allowed per chunk/summary section for context.
        system_instruction (str): System prompt to guide the summarization.

    Returns:
        str: Path to the output JSON file containing chunk summaries.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load document filenames
    with open(doc_filenames_file, "r", encoding="utf-8") as f:
        doc_filenames = json.load(f)

    # Load document summaries (now expecting JSON)
    try:
        with open(summaries_file, "r", encoding="utf-8") as f:
            doc_summaries = json.load(f)
        print(f"✅ Loaded document summaries from JSON: {summaries_file}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error loading document summaries from {summaries_file}: {e}")
        print("Proceeding without document summaries.")
        doc_summaries = {}

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

    for filename in doc_filenames:
        summary = doc_summaries.get(filename, "[No summary available]")
        chunks = merged_grouped_chunks.get(filename, [])

        if not chunks:
            print(f"⚠️ Warning: No chunks found for {filename}")
            continue

        print(f"\n📄 Processing chunks for: {filename} ({len(chunks)} chunks)")

        for i in range(len(chunks)):
            chunk_before = chunks[i - 1] if i > 0 else ""
            target_chunk = chunks[i]
            chunk_after = chunks[i + 1] if i < len(chunks) - 1 else ""

            # Ensure max_words is an integer
            try:
                max_w = int(max_words)
            except ValueError:
                print(
                    f"⚠️ Warning: Invalid max_words value '{max_words}'. Using default 500."
                )
                max_w = 500

            prompt = prompt_template.format(
                summary=truncate(summary, max_w),
                chunk_before=truncate(chunk_before, max_w),
                target_chunk=truncate(target_chunk, max_w),
                chunk_after=truncate(chunk_after, max_w),
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
                print(f"  ✅ Chunk {i}: {result[:80]}...")

            except Exception as e:
                error_msg = f"[ERROR: {str(e)}]"
                print(f"  ❌ Error on chunk {i} in {filename}: {str(e)}")
                chunk_context_summaries[filename].append(error_msg)

    # Write the complete dictionary to the JSON output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dict(chunk_context_summaries), f, ensure_ascii=False, indent=2)

    print(f"\n✅ All chunk-level context summaries written to JSON: '{output_file}'")

    return output_file
