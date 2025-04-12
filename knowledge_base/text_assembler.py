"""
Functions for assembling text for embedding from enhanced chunks.
"""


def assemble_text_for_embedding(chunk: dict) -> dict:
    """
    Assembles text for embedding in a specific format from an enhanced chunk.

    Format:
    ```
    Document Summary
    {doc_summary}

    Document Context Summary
    {context_summary}

    Retrieved Document
    {text}
    ```

    Args:
        chunk (dict): A chunk from enhanced_chunks.json with text and metadata

    Returns:
        dict: A dictionary with the assembled text and original metadata
    """
    text = chunk.get("text", "")
    metadata = chunk.get("metadata", {})

    doc_summary = metadata.get("document_summary", "No document summary available")
    context_summary = metadata.get("chunk_summary", "No context summary available")

    assembled_text = (
        "Document Summary\n"
        f"{doc_summary}\n\n"
        "Document Context Summary\n"
        f"{context_summary}\n\n"
        "Retrieved Document\n"
        f"{text}"
    )

    return {"chunk": assembled_text, "metadata": metadata}


def process_enhanced_chunks(chunks: list) -> list:
    """
    Process a list of enhanced chunks and prepare them for embedding.

    Args:
        chunks (list): List of enhanced chunks from enhanced_chunks.json

    Returns:
        list: List of dictionaries with assembled text and original metadata
    """
    return [assemble_text_for_embedding(chunk) for chunk in chunks]
