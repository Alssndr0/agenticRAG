from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from vlm_options import openai_vlm_options


def convert_pdf_with_vlm(document):
    """
    Convert a PDF document using the OpenAI Vision model for picture descriptions
    and enable table structure detection.

    Args:
        document: The path or object representing the input PDF document.

    Returns:
        ConvertedDocument: The converted document object.
    """
    # Configure pipeline options
    pipeline_options = PdfPipelineOptions(enable_remote_services=True)
    pipeline_options.do_picture_description = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.picture_description_options = openai_vlm_options()

    # Set up and execute the conversion
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
            )
        }
    )

    return doc_converter.convert(document)
