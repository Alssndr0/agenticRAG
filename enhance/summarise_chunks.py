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


def summarise_chunk_contexts(
    doc_filenames,
    summaries,
    merged_grouped_chunks,
    output_file=SUMMARISE_CHUNK_PROMPT,
    model=SUMMARISE_MODEL,
    max_words=500,
    system_instruction="Provide only a very short, succinct context summary for the target text to improve its searchability. Start with 'This chunk details...'",
):
    """
    Generate chunk-level context summaries with a summary and surrounding context.

    Args:
        client: OpenAI client or compatible chat interface.
        doc_filenames (list[str]): List of filenames for tracking.
        summaries (list[str]): Document-level summaries corresponding to each filename.
        merged_grouped_chunks (dict): Dict of filename -> list of text chunks.
        output_file (str): Output file path for saving summaries.
        model (str): LLM model name.
        max_words (int): Max words allowed per chunk/summary section.
        system_instruction (str): System prompt to guide the summarization.

    Returns:
        dict: filename -> list of chunk-level summaries
    """
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
        summary = summaries[doc_filenames.index(filename)]
        chunks = merged_grouped_chunks[filename]

        print(f"\n📄 Processing chunks for: {filename} ({len(chunks)} chunks)")

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

            except Exception as e:
                print(f"  ❌ Error on chunk {i} in {filename}: {str(e)}")
                chunk_context_summaries[filename].append("[ERROR]")

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        for filename, summaries in chunk_context_summaries.items():
            f.write(f"\n📄 Document: {filename}\n")
            for i, summary in enumerate(summaries):
                f.write(f"\nChunk {i}:\n{summary}\n")

    print(f"\n✅ All chunk-level context summaries written to '{output_file}'")
    return chunk_context_summaries
