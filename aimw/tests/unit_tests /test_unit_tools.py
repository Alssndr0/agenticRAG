from unittest.mock import mock_open, patch

from app.services.tools import prepare_document, retrieve_document


def test_retrieve_document_reads_txt(monkeypatch):
    """Test that .txt files are read and returned as string."""
    fake_path = "tests/data/fake.txt"
    fake_content = "hello world"
    monkeypatch.setattr("builtins.open", mock_open(read_data=fake_content))
    assert retrieve_document(fake_path) == fake_content


def test_retrieve_document_reads_md(monkeypatch):
    """Test that .md files are read and returned as string."""
    fake_path = "tests/data/fake.md"
    fake_content = "# Markdown"
    monkeypatch.setattr("builtins.open", mock_open(read_data=fake_content))
    assert retrieve_document(fake_path) == fake_content


def test_retrieve_document_pdf_calls_converter(monkeypatch):
    """Test that .pdf triggers convert_pdf_with_docling."""
    fake_path = "tests/data/fake.pdf"
    with patch(
        "app.services.tools.convert_pdf_with_docling", return_value="mock markdown"
    ) as mock_conv:
        with patch("os.path.splitext", return_value=("tests/data/fake", ".pdf")):
            assert retrieve_document(fake_path) == "mock markdown"
            mock_conv.assert_called_once_with(fake_path)


def test_retrieve_document_unsupported_extension():
    """Test that unsupported extensions return a warning string."""
    result = retrieve_document("file.unsupported")
    assert "[Unsupported file type" in result


def test_retrieve_document_not_found():
    """Test that missing files return placeholder."""
    result = retrieve_document("missing.txt")
    assert "[Placeholder content" in result


def test_retrieve_document_other_exception(monkeypatch):
    """Test generic exception handling."""

    def raise_error(*a, **kw):
        raise Exception("Boom!")

    monkeypatch.setattr("builtins.open", raise_error)
    assert "[Error reading" in retrieve_document("tests/data/fake.txt")


def test_prepare_document_sets_pending_checks():
    """Test that prepare_document returns all CHECKS as pending."""
    fake_state = {"foo": "bar"}
    # Patch CHECKS for predictable output
    with patch("app.services.tools.CHECKS", {"a": 1, "b": 2}):
        result = prepare_document(fake_state)
        assert set(result["pending_checks"]) == {"a", "b"}
        assert result["current_check"] == ""
        assert result["check_results"] == []
