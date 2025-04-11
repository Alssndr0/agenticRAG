import os

from openai import OpenAI

from utils.load_env import get_env_vars

# Get environment variables
ENV = get_env_vars()
SUMMARISE_OUTPUT_FILE = ENV["SUMMARISE_OUTPUT_FILE"]
SUMMARISE_MODEL = ENV["SUMMARISE_MODEL"]
SUMMARISE_DOCUMENT_INPUT_WORDS = ENV["SUMMARISE_DOCUMENT_INPUT_WORDS"]
SUMMARISE_DOCUMENT_PROMPT = ENV["SUMMARISE_DOCUMENT_PROMPT"]


def summarise_documents(
    doc_filenames,
    full_docs,
    output_file=SUMMARISE_OUTPUT_FILE,
    model=SUMMARISE_MODEL,
    summarise_prompt=SUMMARISE_DOCUMENT_PROMPT,
    max_words=SUMMARISE_DOCUMENT_INPUT_WORDS,
):
    """
    Summarises a list of documents using an OpenAI-compatible client.

    Args:
        client: The OpenAI client instance.
        doc_filenames (list[str]): List of filenames corresponding to each document.
        full_docs (list[str]): List of full document texts.
        system_prompt (str): System prompt to guide summarisation.
        output_file (str): File to save summaries to.
        model (str): The model to use (e.g., "gpt-4o").
        max_words (int): Max number of words per document (truncates if longer).

    Returns:
        list[str]: List of generated summaries.
    """
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

    return summaries
