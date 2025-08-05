import uuid

from loguru import logger

from app.services.graph import graph
from app.services.tools import retrieve_document


def run_compliance_check(
    document_path: str, question: str = "Please check my document for compliance."
):
    """
    Run the complete compliance checking workflow.

    Args:
        document_path (str): Path to the document to check
        question (str): Optional question/context for the check

    Returns:
        dict: Final state with compliance results
    """
    logger.info(f"Starting compliance check for document: {document_path}")

    # Initialize state
    init_state = {
        "document": retrieve_document(document_path),
        "comparison_document": "",
        "pending_checks": [],
        "current_check": "",
        "check_results": [],
        "question": question,
        "answer": "",
    }

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    # Run the workflow
    result = graph.invoke(init_state, config=config)
    return result
