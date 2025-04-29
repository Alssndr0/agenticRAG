import json
import os

from openai import OpenAI

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()

SUMMARISE_OUTPUT_FILE = ENV["SUMMARISE_OUTPUT_FILE"]
SUMMARISE_MODEL = ENV["SUMMARISE_MODEL"]
SUMMARISE_DOCUMENT_INPUT_WORDS = int(ENV["SUMMARISE_DOCUMENT_INPUT_WORDS"])
SUMMARISE_DOCUMENT_PROMPT = ENV["SUMMARISE_DOCUMENT_PROMPT"]
DOC_FILENAMES_FILE = ENV["DOC_FILENAMES_FILE"]
FULL_DOCS_FILE = ENV["FULL_DOCS_FILE"]


def summarise_documents(
    doc_filenames_file=DOC_FILENAMES_FILE,
    full_docs_file=FULL_DOCS_FILE,
    output_file=SUMMARISE_OUTPUT_FILE,
    model=SUMMARISE_MODEL,
    summarise_prompt=SUMMARISE_DOCUMENT_PROMPT,
    max_words=SUMMARISE_DOCUMENT_INPUT_WORDS,
):
    """
    Summarises documents using an OpenAI-compatible client and writes summaries to a JSON file.

    Args:
        doc_filenames_file (str): Path to JSON file containing document filenames.
        full_docs_file (str): Path to JSON file containing full document texts.
        output_file (str): JSON file to save summaries to (filename -> summary mapping).
        model (str): The model to use (e.g., "gpt-4o").
        summarise_prompt (str): System prompt for summarization.
        max_words (int): Max number of words per document (truncates if longer).

    Returns:
        str: Path to the output JSON file containing summaries.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load document filenames and full docs from files
    with open(doc_filenames_file, "r", encoding="utf-8") as f:
        doc_filenames = json.load(f)

    with open(full_docs_file, "r", encoding="utf-8") as f:
        full_docs = json.load(f)

    summaries_dict = {}

    for i, (filename, doc) in enumerate(zip(doc_filenames, full_docs)):
        print(f"📝 Summarizing document {i + 1}: {filename}")

        # Truncate the document to first `max_words` words
        words = doc.split()
        truncated_doc = " ".join(words[: int(max_words)])
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
            summaries_dict[filename] = summary

            print(f"  ✅ Summary: {summary[:80]}...")

        except Exception as e:
            print(f"  ❌ Error for document '{filename}': {str(e)}")
            summaries_dict[filename] = "[ERROR: Could not generate summary]"

    # Save to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summaries_dict, f, ensure_ascii=False, indent=2)

    print(f"\n✅ All summaries (with truncation) written to '{output_file}'")

    return output_file
