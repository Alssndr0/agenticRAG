from agent import convert_pdf_with_docling, graph
from langchain_core.messages import AIMessage
import gradio as gr

# This function is called ONLY when PDF is uploaded/processed.
def convert_and_cache_pdf(file):
    markdown = convert_pdf_with_docling(file)
    return markdown

# This function is called every time a question is asked.
def answer_question(markdown, question):
    initial_state = {
        "document": markdown,
        "question": question,
        "document_size": 0,
        "document_chunks": [],
        "current_chunk": 0,
        "observations": [],
        "answer": "",
    }
    thinking = ""
    final_answer = ""
    for token, metadata in graph.stream(
        initial_state,
        {"recursion_limit": 1000},
        stream_mode="messages"
    ):
        if isinstance(token, AIMessage):
            node = metadata.get("langgraph_node")
            if node == "agent_observe":
                thinking += token.content
                # Yield (final_answer, thinking, clear input)
                yield final_answer, f"**Agent thinking:**\n{thinking}", ""
            elif node == "reviewer":
                final_answer += token.content
                yield final_answer, f"**Agent thinking:**\n{thinking}", ""
            else:
                yield final_answer, f"[{node}]\n{token.content}", ""
    yield final_answer, f"**Agent thinking:**\n{thinking}", ""
