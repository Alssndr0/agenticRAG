import os

import pytest
from app.services.extract_pdf import convert_pdf_with_docling


@pytest.mark.integration
def test_convert_pdf_with_docling_real_pdf():
    """Verify that convert_pdf_with_docling processes a real PDF and returns non-empty markdown containing expected keywords."""
    pdf_path = "../data/bill_of_lading.pdf"
    assert os.path.isfile(pdf_path), f"Sample PDF not found: {pdf_path}"

    markdown = convert_pdf_with_docling(pdf_path)
    # The output should be a string, not empty, and likely contain a word from your PDF.
    assert isinstance(markdown, str)
    assert len(markdown) > 0
    assert "Disputes" in markdown or "disputes" in markdown
