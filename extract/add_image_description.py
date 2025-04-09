from typing import List

from docling_core.types.doc.document import PictureItem


def insert_image_descriptions(
    markdown_text: str, picture_items: List[PictureItem]
) -> str:
    """
    Inserts image descriptions from picture_items into markdown text.

    Finds '<!-- image -->' tags in the markdown and inserts the description
    from the corresponding PictureItem immediately after it, preceded by
    'image_description: '.

    Args:
        markdown_text: The markdown content as a string.
        picture_items: A list of PictureItem objects, each containing
                       at least one annotation with description text.
                       The order must match the order of '<!-- image -->' tags.

    Returns:
        The modified markdown string with descriptions inserted.

    Raises:
        AssertionError: If the number of '<!-- image -->' tags does not
                        match the number of items in picture_items.
        RuntimeError: If placeholder tags cannot be found sequentially as expected.
        # Note: ValueError previously mentioned for missing annotations/text
        # is now handled with warnings and default text, but could be reinstated.
    """
    image_placeholder = "<!-- image -->"
    image_description_prefix = "image_description:"

    # 1. Count occurrences
    image_tag_count = markdown_text.count(image_placeholder)
    description_count = len(picture_items)

    # 2. Assert counts match
    assert image_tag_count == description_count, (
        f"Mismatch: Found {image_tag_count} '{image_placeholder}' tags "
        f"but received {description_count} picture items."
    )

    # 3. Iterate and replace sequentially
    current_markdown = markdown_text
    last_pos = 0  # Keep track of where to search from for the next placeholder

    for i in range(description_count):
        # Find the *next* placeholder starting from after the last one found
        placeholder_pos = current_markdown.find(image_placeholder, last_pos)

        if placeholder_pos == -1:
            # This shouldn't happen if the initial count was correct, but defensive check
            raise RuntimeError(
                f"Error: Could not find placeholder instance {i + 1} after position {last_pos}. "
                "Markdown may have been modified unexpectedly."
            )

        # Get the description text safely
        if not picture_items[i].annotations:
            # Handle case with no annotations for a picture item
            print(
                f"Warning: PictureItem index {i} has no annotations. Using default text."
            )
            description_text = "No description available."
            # Or raise ValueError("PictureItem index {} has no annotations.".format(i))
        else:
            # Assuming the first annotation is the relevant description
            first_annotation = picture_items[i].annotations[0]
            if hasattr(first_annotation, "text") and first_annotation.text:
                description_text = (
                    first_annotation.text.strip()
                )  # Remove leading/trailing whitespace
            else:
                # Handle case where the annotation exists but has no text
                print(
                    f"Warning: Annotation for PictureItem index {i} has no text. Using default text."
                )
                description_text = "Description text missing."
                # Or raise ValueError("Annotation for PictureItem index {} has no text.".format(i))

        # Perform the replacement by inserting *after* the placeholder
        # Find the end of the placeholder tag
        placeholder_end_pos = placeholder_pos + len(image_placeholder)

        # Define the text to insert (adding newlines for readability)
        inserted_text = f"{image_description_prefix} {description_text}\n"

        # Build the new string by slicing and inserting
        current_markdown = (
            current_markdown[
                :placeholder_end_pos
            ]  # Part before and including placeholder
            + inserted_text  # The inserted description text
            + current_markdown[placeholder_end_pos:]  # The rest of the string
        )

        # Update last_pos to search *after* the inserted text for the next placeholder
        # We need to account for the length of the text we just added.
        last_pos = placeholder_end_pos + len(inserted_text)

    # 4. Return the modified string
    return current_markdown
