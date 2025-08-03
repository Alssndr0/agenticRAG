from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import AIMessage
from IPython.display import Image, display
from langgraph.graph.message import add_messages

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

def split_markdown(markdown, max_tokens=500):
    """Split markdown into chunks under max_tokens."""
    words = markdown.split()
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(current) >= max_tokens:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


# LLM setup (LM Studio)
llm = ChatOpenAI(
    openai_api_base="http://localhost:1234/v1",
    openai_api_key="not-needed",
    model_name="qwen3-30b-a3b-instruct-2507-mlx",
)

# State schema for LangGraph
class AgentState(TypedDict):
    document: str
    document_chunks: list[str]
    current_chunk: int
    question: str
    observations: Annotated[list[str], add_messages]
    answer: str
    document_size: int

class Context(TypedDict):
    user_id: float

def prepare_document(state: AgentState) -> AgentState:
    markdown = state["document"]
    tokens = len(markdown.split())
    # Only update these fields
    document_size = tokens
    if tokens > 5000:
        document_chunks = split_markdown(markdown, max_tokens=5000)
        current_chunk = 0
    else:
        document_chunks = [markdown]
        current_chunk = 0
    
    return {
        "document_chunks": document_chunks,
        "current_chunk": current_chunk,
        "document_size": document_size,
    }

def agent_observe_node(state: AgentState):
    chunk = state["document_chunks"][state["current_chunk"]]
    question = state["question"]
    obs = llm.invoke(
        f"Read this chunk and note if there is any information useful for answering the question'{question}':\n\n{chunk}. \nKeep your notes concise and relevant."
    )
    # Copy to avoid mutation if needed
    new_observations = state["observations"] + [obs.content]
    current_chunk = state["current_chunk"] + 1
    return {
        "observations": new_observations,
        "current_chunk": current_chunk
    }

def should_continue_node(state: AgentState):
    """Decide whether to continue processing chunks or move to the next step."""
    # This function is used for conditional routing, so it should return the routing decision
    if state["current_chunk"] < len(state["document_chunks"]):
        return "agent_observe"
    else:
        return "reviewer"

def reviewer_node(state: AgentState):
    question = state["question"]
    prompt = f"Based on these notes, answer the question '{question}':\n\n{state['observations']}.\n\nAnswer in a general way, as if you had read the entire document rather than the notes."
    answer_chunks = []
    for token in llm.stream(prompt):
        if hasattr(token, "content"):
            answer_chunks.append(token.content)
    answer = "".join(answer_chunks)
    return {"answer": answer}


builder = StateGraph(state_schema=AgentState, context_schema=Context)
builder.add_node("prepare_document", prepare_document)
builder.add_node("agent_observe", agent_observe_node)
builder.add_node("reviewer", reviewer_node)

# Chain the flow
builder.add_edge(START, "prepare_document")
builder.add_edge("prepare_document", "agent_observe")
builder.add_conditional_edges(
    "agent_observe",
    should_continue_node,
    {
        "agent_observe": "agent_observe",
        "reviewer": "reviewer"
    }
)
builder.add_edge("reviewer", END)

graph = builder.compile()
