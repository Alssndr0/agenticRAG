import asyncio
import uuid
from typing import Any, AsyncGenerator, Dict, Tuple

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from loguru import logger

from app.services.extract_pdf import convert_pdf_with_docling
from app.services.graph import graph


# This function is called when PDF is uploaded/processed.
def convert_and_cache_pdf(file) -> str:
    markdown = convert_pdf_with_docling(file)
    return markdown


async def run_compliance_check(
    document_content: str, question: str = "Please check my document for compliance."
) -> AsyncGenerator[Tuple[str, str, str], None]:
    """
    Runs the compliance check by streaming the agent's thoughts, then
    retrieves the final state of that same run without a second execution.
    """
    logger.info("Starting compliance check")
    init_state: Dict[str, Any] = {
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
    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 500,
    }

    thinking = ""
    last_thinking_yield = ""

    # Stream the agent's thoughts.
    async for token, metadata in graph.astream(
        init_state,  # type: ignore
        config,
        stream_mode="messages",
    ):
        if isinstance(token, AIMessage):
            # Fix 2: Add type check for metadata to ensure it's a dict
            if isinstance(metadata, dict):
                node = metadata.get("langgraph_node", "")
                if node == "agent_executor":
                    # Fix 3: Ensure token.content is a string before concatenating
                    content = token.content
                    if isinstance(content, str):
                        thinking += content
                    elif isinstance(content, list):
                        # Handle case where content might be a list of strings or dicts
                        for item in content:
                            if isinstance(item, str):
                                thinking += item
                            elif isinstance(item, dict) and "text" in item:
                                thinking += str(item["text"])
                    else:
                        thinking += str(content)

                    last_thinking_yield = (
                        f"**Compliance Agent is checking:**\n{thinking}"
                    )
                    yield "", last_thinking_yield, ""

    # Get the final answer from the same run's state
    final_state_obj = graph.get_state(config)
    final_answer = ""
    values = getattr(final_state_obj, "values", None)
    if isinstance(values, dict):
        final_answer = values.get("answer", "No answer found.")
    else:
        final_answer = "No answer found."

    if not isinstance(final_answer, str):
        final_answer = str(final_answer)

    # Stream the final answer word by word
    left_stream = ""
    words = final_answer.split()

    for i, word in enumerate(words):
        # Add space before word (except for the first word)
        if i > 0:
            left_stream += " "

        left_stream += word
        yield left_stream, last_thinking_yield, ""
        await asyncio.sleep(0.005)  # 200ms between words

    yield final_answer, last_thinking_yield, ""
