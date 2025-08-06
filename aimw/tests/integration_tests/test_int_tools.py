import os

import pytest
from app.services.tools import retrieve_document


@pytest.mark.integration
def test_retrieve_document_reads_real_txt():
    """Integration: reads a real .txt file."""
    txt_path = "../data/bill_of_lading.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Integration test text")
    content = retrieve_document(txt_path)
    assert "Integration test text" in content
    os.remove(txt_path)


@pytest.mark.integration
def test_retrieve_document_reads_real_pdf():
    """Integration: reads a real PDF and converts to markdown (requires working extract_pdf)."""
    pdf_path = "tests/data/sample.pdf"
    # Place a small sample.pdf in tests/data/ for this test!
    markdown = retrieve_document(pdf_path)
    assert isinstance(markdown, str)
    assert len(markdown) > 0
