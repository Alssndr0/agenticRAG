import os
import sys

import joblib

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from base_chunker import chunk_markdown

with open("data/extracted/output.joblib", "rb") as f:
    markdown_file = joblib.load(f)

chunked_markdown = chunk_markdown(
    markdown_file, chunk_size=400, chunk_overlap=0, delimiter=".\n\n\n"
)

for chunk in chunked_markdown:
    print(chunk)
    print("-" * 100)
