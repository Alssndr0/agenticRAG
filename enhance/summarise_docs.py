import json
import os

from openai import OpenAI

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
SUMMARISE_OUTPUT_FILE = ENV["SUMMARISE_OUTPUT_FILE"]
SUMMARISE_MODEL = ENV["SUMMARISE_MODEL"]
SUMMARISE_DOCUMENT_INPUT_WORDS = ENV["SUMMARISE_DOCUMENT_INPUT_WORDS"]
SUMMARISE_DOCUMENT_PROMPT = ENV["SUMMARISE_DOCUMENT_PROMPT"]
DOC_FILENAMES_FILE = ENV.get("DOC_FILENAMES_FILE", "data/enhance/doc_filenames.json")
FULL_DOCS_FILE = ENV.get("FULL_DOCS_FILE", "data/enhance/full_docs.json")


def summarise_documents(
    doc_filenames_file=DOC_FILENAMES_FILE,
    full_docs_file=FULL_DOCS_FILE,
    output_file=SUMMARISE_OUTPUT_FILE,
    model=SUMMARISE_MODEL,
    summarise_prompt=SUMMARISE_DOCUMENT_PROMPT,
    max_words=SUMMARISE_DOCUMENT_INPUT_WORDS,
):
    """
    Summarises documents using an OpenAI-compatible client and writes to file.

    Args:
        doc_filenames_file (str): Path to JSON file containing document filenames.
        full_docs_file (str): Path to JSON file containing full document texts.
        output_file (str): File to save summaries to.
        model (str): The model to use (e.g., "gpt-4o").
        summarise_prompt (str): System prompt for summarization.
        max_words (int): Max number of words per document (truncates if longer).

    Returns:
        str: Path to the output file containing summaries.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load document filenames and full docs from files
    with open(doc_filenames_file, "r", encoding="utf-8") as f:
        doc_filenames = json.load(f)

    with open(full_docs_file, "r", encoding="utf-8") as f:
        full_docs = json.load(f)

    summaries = []

    for i, (filename, doc) in enumerate(zip(doc_filenames, full_docs)):
        print(f"📝 Summarizing document {i + 1}: {filename}")

        # Truncate the document to first `max_words` words
        words = doc.split()
        truncated_doc = " ".join(words[:max_words])
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": summarise_prompt},
                    {"role": "user", "content": truncated_doc},
                ],
            )

            summary = response.choices[0].message.content.strip()
            summaries.append(summary)

            print(f"  ✅ Summary: {summary[:80]}...")

        except Exception as e:
            print(f"  ❌ Error for document '{filename}': {str(e)}")
            summaries.append("[ERROR: Could not generate summary]")

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        for filename, summary in zip(doc_filenames, summaries):
            f.write(f"{filename}:\n{summary}\n\n")

    print(f"\n✅ All summaries (with truncation) written to '{output_file}'")

    return output_file
