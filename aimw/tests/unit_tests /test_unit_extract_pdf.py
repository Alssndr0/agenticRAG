from unittest.mock import MagicMock, patch

import pytest
from app.services.extract_pdf import convert_pdf_with_docling


@pytest.fixture
def fake_pdf_path():
    return "tests/data/fake.pdf"


def test_convert_pdf_with_docling_returns_markdown(fake_pdf_path):
    """Test that convert_pdf_with_docling returns markdown string output."""
    mock_docling_obj = MagicMock()
    mock_docling_obj.convert.return_value.document.export_to_markdown.return_value = (
        "# Mock PDF Content"
    )

    with patch(
        "app.services.extract_pdf.DocumentConverter", return_value=mock_docling_obj
    ):
        with patch("app.services.extract_pdf.InputFormat"):
            with patch("app.services.extract_pdf.PdfFormatOption"):
                result = convert_pdf_with_docling(fake_pdf_path)
                assert isinstance(result, str)
                assert "# Mock PDF Content" in result


def test_convert_pdf_with_docling_calls_converter(fake_pdf_path):
    """Test that DocumentConverter and export_to_markdown are called."""
    with patch("app.services.extract_pdf.DocumentConverter") as MockConverter:
        instance = MockConverter.return_value
        mock_export = MagicMock(return_value="# Markdown")
        instance.convert.return_value.document.export_to_markdown = mock_export

        with patch("app.services.extract_pdf.InputFormat"):
            with patch("app.services.extract_pdf.PdfFormatOption"):
                convert_pdf_with_docling(fake_pdf_path)
                assert instance.convert.called
                assert mock_export.called


def test_convert_pdf_with_docling_handles_empty_file():
    """Test that convert_pdf_with_docling raises an Exception for an invalid PDF."""
    with patch("app.services.extract_pdf.DocumentConverter") as MockConverter:
        MockConverter.return_value.convert.side_effect = Exception("Invalid PDF")
        with patch("app.services.extract_pdf.InputFormat"):
            with patch("app.services.extract_pdf.PdfFormatOption"):
                with pytest.raises(Exception):
                    convert_pdf_with_docling("badfile.pdf")
