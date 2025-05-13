from app.schemas.request import RetrieveRequest
from app.services.answer import lumera_llm
from app.services.format import (
    format_retrieved_docs_for_response,
    format_retrieved_documents,
)
from app.services.retrieve import HybridRetriever
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

router = APIRouter()


@router.post("/retrieve-and-answer")
async def retrieve_and_answer(request: Request, question_request: RetrieveRequest):
    try:
        logger.info(
            f"Received question: {question_request.query}, k: {question_request.k},\
                alpha: {question_request.alpha}, filters: {question_request.filters}"
        )

        # Retrieve the HybridRetriever instance from app state.
        retriever: HybridRetriever = request.app.state.retriever

        # Step 1: Retrieve documents.
        retrieved_docs = retriever.search(
            query=question_request.query,
            k=question_request.k,
            metadata_filter=question_request.filters,
            alpha=question_request.alpha,
        )
        # logger.info(f"Retrieved documents: {retrieved_docs}")

        # Step 2: Format the retrieved documents for the LLM prompt.
        formatted_docs = format_retrieved_documents(retrieved_docs)

        # Retrieve the shared InferenceClient from app state.
        inference_client = request.app.state.inference_client

        # Use custom prompt if provided, otherwise use default
        custom_system = question_request.system

        # Step 3: Query the LLM using the shared lumera_llm function.
        llm_response = lumera_llm(
            documents=formatted_docs,
            question=question_request.query,
            max_new_tokens=None,
            stream=None,
            client=inference_client,
            custom_system=custom_system,  # Pass the custom system prompt
        )
        logger.info(f"LLM response: {llm_response}")

        # Step 4: Format the retrieved documents for the API response.
        formatted_retrieved_docs = format_retrieved_docs_for_response(retrieved_docs)

        # Step 5: Return the answer and document details.
        return {"answer": llm_response, "retrieved_documents": formatted_retrieved_docs}

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing request: {e}")


@router.get("/health")
def health_check():
    return {"status": "OK"}
