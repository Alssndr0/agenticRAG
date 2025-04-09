import os
import sys

import joblib

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import using relative imports for files in the same directory
from add_image_description import insert_image_descriptions

from extract import convert_pdf_with_vlm

extraction = convert_pdf_with_vlm(
    "/Users/alessandro/Development/generalRAG/data/original/Fact-Sheets.pdf"
)
markdown_image = insert_image_descriptions(
    extraction.document.export_to_markdown(), extraction.document.pictures
)

# Save
joblib.dump(markdown_image, "output.joblib")
