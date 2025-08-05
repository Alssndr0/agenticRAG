from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption


def convert_pdf_with_docling(document):
    """
    Convert a PDF document.

    Args:
        document: The path or object representing the input PDF document.

    Returns:
        ConvertedDocument: The converted document object.
    """
    # Configure pipeline options
    pipeline_options = PdfPipelineOptions(enable_remote_services=False)
    pipeline_options.do_picture_description = False
    pipeline_options.do_table_structure = False
    pipeline_options.table_structure_options.do_cell_matching = False

    # Set up and execute the conversion
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )
    document = doc_converter.convert(document).document
    markdown = document.export_to_markdown()
    return markdown
