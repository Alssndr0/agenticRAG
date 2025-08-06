import uuid

from langchain_core.runnables import RunnableConfig
from loguru import logger

from app.schemas.agent_schemas import AgentState
from app.services.graph import graph
from app.services.tools import retrieve_document


def run_compliance_check(
    document_path: str, question: str = "Please check my document for compliance."
) -> dict:
    """
    Run the complete compliance checking workflow.

    Args:
        document_path (str): Path to the document to check
        question (str): Optional question/context for the check

    Returns:
        dict: Final state with compliance results
    """
    logger.info(f"Starting compliance check for document: {document_path}")

    # Prepare state to exactly match AgentState schema
    init_state: AgentState = {
        "document": retrieve_document(document_path),
        "comparison_document": "",
        "pending_checks": [],
        "current_check": "",
        "check_results": [],
        "question": question,
        "answer": "",
    }

    config: RunnableConfig = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke(init_state, config=config)
    return result
