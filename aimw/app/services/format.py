def format_retrieved_json(retrieved_json: dict) -> str:
    """
    Formats questionnaire documents in a question-answer format to be used by the LLM.

    Args:
        retrieved_iso_json (dict): A dictionary of documents where keys are document IDs,
                                   and values contain the question and answer.

    Returns:
        str: A formatted string with questions and answers.
    """
    formatted_docs = []

    for doc_id, doc in retrieved_json.items():
        question = doc.get("question", "")
        answer = doc.get("answer", "")
        if question and answer:
            formatted_docs.append(f"Question: {question}\nAnswer: {answer}\n")

    # Join all formatted questions and answers into a single string
    return "\n".join(formatted_docs)


def format_retrieved_documents(retrieved_docs: list) -> str:
    formatted_docs = []
    for doc in retrieved_docs:
        metadata = doc.get("metadata", {})
        question = metadata.get("question", "No question available")
        answer = metadata.get("answer", "No answer available")
        formatted_docs.append(f"Question: {question}\nAnswer: {answer}\n")
    return "\n".join(formatted_docs)


def format_retrieved_docs_for_response(retrieved_docs: list) -> list:
    """
    Formats the list of retrieved documents for the API response.
    """
    formatted_docs = []
    for doc in retrieved_docs:
        metadata = doc.get("metadata", {})
        formatted_docs.append(
            {
                "question": metadata.get("question", "No question available"),
                "answer": metadata.get("answer", "No answer available"),
                "metadata": {
                    "id": metadata.get("id", ""),
                    "createdBy": metadata.get("createdBy", ""),
                    "createdDate": metadata.get("createdDate", ""),
                    "area": metadata.get("area", ""),
                    "source": metadata.get("source", ""),
                    "last_modified": metadata.get("lastDateModified", ""),
                    "category": metadata.get("category", ""),
                },
                "score": doc.get("score", 0),
                "retrieval_method": doc.get("retrieval_method", ""),
            }
        )
    return formatted_docs


def format_retrieved_json_for_questionnaire(retrieved_json: dict) -> str:
    """
    Formats questionnaire documents in a question-answer format to be used by the LLM.

    Args:
        retrieved_iso_json (dict): A dictionary of documents where keys are document IDs,
                                   and values contain the question and answer.

    Returns:
        str: A formatted string with questions and answers.
    """
    formatted_docs = []

    for doc in retrieved_json:
        metadata = doc.get("metadata", {})
        question = metadata.get("question", "")
        answer = metadata.get("answer", "")

        if question and answer:
            formatted_docs.append(f"Question: {question}\nAnswer: {answer}\n")

    # Join all formatted questions and answers into a single string
    return "\n".join(formatted_docs)
