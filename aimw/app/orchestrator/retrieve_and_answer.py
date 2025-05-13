from app.schemas.request import RetrieveRequest
from app.services.answer import lumera_llm
from app.services.format import (format_retrieved_docs_for_response,
                                 format_retrieved_json_for_questionnaire)
from app.services.retrieve import HybridRetriever
from app.state import get_inference_client, get_retriever
from fastapi import HTTPException
from loguru import logger


def retrieve_and_answer_logic(question_request: RetrieveRequest):
    """
    Orchestrates document retrieval and LLM answering.

    Args:
        request: The FastAPI request object (used to access app.state).
        question_request: The request payload containing the question, k, and alpha.

    Returns:
        A dict with the LLM answer and formatted retrieved documents.
    """
    try:
        logger.info(
            f"Received question: {question_request.query}, k: {question_request.k}, alpha: {question_request.alpha}"
        )

        # Retrieve the HybridRetriever instance from app state.
        retriever: HybridRetriever = get_retriever()

        # Step 1: Retrieve documents.
        retrieved_docs = retriever.search(
            query=question_request.query,
            k=question_request.k,
            alpha=question_request.alpha,
        )
        # logger.info(f"Retrieved documents: {retrieved_docs}")
        logger.info("Retrieved documents")

        # Step 2: Format the retrieved documents for the LLM prompt.
        formatted_docs = format_retrieved_json_for_questionnaire(retrieved_docs)
        logger.info("Formatted documents for LLM")

        # Retrieve the shared InferenceClient from app state.
        inference_client = get_inference_client()

        # Step 3: Query the LLM using the shared lumera_llm function.
        llm_response = lumera_llm(
            documents=formatted_docs,
            question=question_request.query,
            max_new_tokens=None,  # Defaults to settings if None
            stream=None,  # Defaults to settings if None
            client=inference_client,
        )
        logger.info("LLM response recieved")

        # Step 4: Format the retrieved documents for the API response.
        formatted_retrieved_docs = format_retrieved_docs_for_response(retrieved_docs)
        # logger.info(f"Formatted documents for API response: {formatted_retrieved_docs}")

        # Step 5: Return the answer and document details.
        return {"answer": llm_response, "retrieved_documents": formatted_retrieved_docs}

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {e}"
        ) from e
