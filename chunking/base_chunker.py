from typing import List


def chunk_markdown(
    markdown_text: str,
    chunk_size: int = 400,
    chunk_overlap: int = 0,
    delimiter: str = ".\n\n\n",
) -> List[str]:
    """
    Chunks markdown text based on a specified delimiter with configurable chunk size and overlap.

    Args:
        markdown_text: The markdown text to chunk
        chunk_size: Target number of words per chunk
        chunk_overlap: Number of words to overlap between chunks
        delimiter: The delimiter to split on, defaults to ".\n"

    Returns:
        A list of text chunks
    """
    # Split the text by the delimiter
    segments = markdown_text.split(delimiter)

    # Add the delimiter back to each segment except the last one
    segments = [segment + delimiter for segment in segments[:-1]] + [segments[-1]]

    chunks = []
    current_chunk = []
    current_chunk_word_count = 0

    # Process each segment
    for segment in segments:
        segment_words = segment.split()
        segment_word_count = len(segment_words)

        # If adding this segment exceeds the chunk size and we already have content,
        # finalize the current chunk and start a new one
        if current_chunk_word_count + segment_word_count > chunk_size and current_chunk:
            chunks.append(delimiter.join(current_chunk).strip())

            # Calculate overlap words to keep
            if chunk_overlap > 0 and current_chunk:
                # Get the last chunk's content and extract the overlap
                last_chunk_text = current_chunk[-1]
                last_chunk_words = last_chunk_text.split()

                # If the last segment has enough words for the overlap
                if len(last_chunk_words) >= chunk_overlap:
                    overlap_text = " ".join(last_chunk_words[-chunk_overlap:])
                    current_chunk = [overlap_text]
                    current_chunk_word_count = chunk_overlap
                else:
                    # If not enough words in the last segment, carry over the whole segment
                    current_chunk = [last_chunk_text]
                    current_chunk_word_count = len(last_chunk_words)
            else:
                current_chunk = []
                current_chunk_word_count = 0

        # Add the current segment to the chunk
        current_chunk.append(segment)
        current_chunk_word_count += segment_word_count

    # Add the last chunk if there's anything left
    if current_chunk:
        chunks.append(delimiter.join(current_chunk).strip())

    return chunks
