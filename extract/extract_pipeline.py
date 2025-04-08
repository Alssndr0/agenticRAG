import os
import sys

import joblib

# Add the directory containing this script to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from extract import convert_pdf_with_vlm

extraction = convert_pdf_with_vlm(
    "/Users/alessandro/Development/generalRAG/data/original/Fact-Sheets.pdf"
)

# Save
joblib.dump(extraction, "output.joblib")
