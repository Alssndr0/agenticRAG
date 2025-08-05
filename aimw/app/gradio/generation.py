import time
import uuid

from langchain_core.messages import AIMessage
from loguru import logger

from app.services.extract_pdf import convert_pdf_with_docling
from app.services.graph import graph


# This function is called when PDF is uploaded/processed.
def convert_and_cache_pdf(file):
    markdown = convert_pdf_with_docling(file)
    return markdown


def run_compliance_check(
    document_content: str, question: str = "Please check my document for compliance."
):
    """
    Runs the compliance check by streaming the agent's thoughts, then
    retrieves the final state of that same run without a second execution.
    """
    logger.info("Starting compliance check")
    init_state = {
        "document": document_content,
        "comparison_document": "",
        "pending_checks": [],
        "current_check": "",
        "check_results": [],
        "question": question,
        "answer": "",
    }

    # Create a unique ID for this specific run.
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 500,
    }

    thinking = ""
    last_thinking_yield = ""

    # Stream all "thinking" tokens. With a checkpointer set, the graph
    # will now automatically save the state for the given thread_id.
    for token, metadata in graph.stream(init_state, config, stream_mode="messages"):
        if isinstance(token, AIMessage):
            node = metadata.get("langgraph_node", "")
            if node == "agent_executor":
                thinking += token.content
                last_thinking_yield = f"**Compliance Agent is checking:**\n{thinking}"
                yield "", last_thinking_yield, ""

    # Once the stream is done, retrieve the final state of that run.
    # This now works because the checkpointer has saved the state.
    final_state_obj = graph.get_state(config)
    final_answer = final_state_obj.values.get("answer", "No answer found.")

    # Animate the final answer.
    left_stream = ""
    for char in final_answer:
        left_stream += char
        yield left_stream, last_thinking_yield, ""
        time.sleep(0.0005)

    yield final_answer, last_thinking_yield, ""
