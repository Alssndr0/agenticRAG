import os
import sys

# Add the parent directory to sys.path to allow importing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List

from openai import OpenAI
from sentence_transformers import SentenceTransformer

# Use conditional import to handle both direct execution and module import
try:
    # When imported as a module
    from .hybrid_retriever import HybridRetriever
except ImportError:
    # When run directly
    from hybrid_retriever import HybridRetriever

from utils.load_env import get_env_vars

env = get_env_vars()

# Check for required environment variables
required_env_vars = ["OPENAI_API_KEY"]
missing_vars = [var for var in required_env_vars if var not in env or not env[var]]
if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )

api_key = env["OPENAI_API_KEY"]
embeddings_model_name = env.get("EMBED_MODEL_ID", "Alibaba-NLP/gte-Qwen2-7B-instruct")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)


def initialize_embeddings_model(
    model_name: str = embeddings_model_name,
) -> SentenceTransformer:
    """Initialize and return a sentence transformer model for embeddings."""
    try:
        model = SentenceTransformer(model_name)
        print(f"Loaded embeddings model: {model_name}")
        return model
    except Exception as e:
        raise ValueError(f"Failed to load embeddings model '{model_name}': {str(e)}")


def initialize_retriever(
    embeddings_model: SentenceTransformer = None,
    faiss_index_path: str = env.get(
        "FAISS_INDEX_PATH",
        "/Users/alessandro/Development/generalRAG/indexes/FAISS-TEST/enhanced_chunks_20250412_193515",
    ),
    bm25_index_path: str = env.get(
        "BM25_INDEX_PATH",
        "/Users/alessandro/Development/generalRAG/indexes/bm25/bm25_index_20250412_193515.pkl",
    ),
) -> HybridRetriever:
    """Initialize the hybrid retriever with the specified index paths and embeddings model."""
    if embeddings_model is None:
        embeddings_model = initialize_embeddings_model()

    return HybridRetriever(
        faiss_index_path=faiss_index_path,
        bm25_index_path=bm25_index_path,
        model_embeddings=embeddings_model,
    )


def create_history(
    conversation_history: List[Dict[str, str]], user_input: str, assistant_response: str
) -> List[Dict[str, str]]:
    """Add a user-assistant exchange to the conversation history."""
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": assistant_response})
    return conversation_history


def generate_response(
    question: str,
    retriever: HybridRetriever,
    model: str = env.get("OPENAI_MODEL", "gpt-4o-mini"),
    k: int = 2,
    alpha: float = 0.7,
) -> str:
    """
    Generate a response to a question using retrieved context and an LLM.

    Args:
        question: The user's question
        retriever: The retriever to use for context
        model: The OpenAI model to use
        k: Number of documents to retrieve
        alpha: Weight between FAISS and BM25 (1.0 = only FAISS, 0.0 = only BM25)

    Returns:
        The generated response
    """
    try:
        # Retrieve relevant documents
        retrieved = retriever.search(query=question, k=k, alpha=alpha)

        if not retrieved:
            return "No relevant documents found for this query."

        # Format context for the prompt
        context = "\n\n".join(
            [
                f"Document: {doc['metadata'].get('filename', 'Unknown')}, Page: {doc['metadata'].get('pages', 'N/A')}\n"
                f"Content: {doc['chunk']}"
                for doc in retrieved
            ]
        )
        print(f"Retrieved:\n {context}")

        # Create the prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on the provided documentation.",
            },
            {
                "role": "user",
                "content": f"Given the provided documentation:\n{context}\n\n"
                f"Answer the following question, being careful to only report factual data found in the documents:\n{question}\n\n"
                f"In your response cite the name of the document and page you got that info from, in this format (Document name, page: )",
            },
        ]

        print(f"Using OpenAI model: {model}")

        # Generate response
        response = client.chat.completions.create(
            model=model, messages=messages, max_tokens=1000
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"Detailed error:\n{error_details}")

        # Provide helpful advice based on the error
        if "invalid model ID" in str(e):
            available_models = ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o-mini"]
            return (
                f"Error with OpenAI model '{model}'. This model may not be available to your account.\n"
                f"Try one of these models instead: {', '.join(available_models)}\n"
                f"Update your .env file or pass a different model to the function."
            )

        return f"Error generating response: {str(e)}"


def main():
    try:
        # Initialize the embeddings model
        print("Initializing embeddings model...")
        embeddings_model = initialize_embeddings_model()

        # Initialize the retriever
        print("Initializing hybrid retriever...")
        retriever = initialize_retriever(embeddings_model=embeddings_model)

        # Initialize conversation history
        conversation_history = []

        # Example question or get from command line
        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])
        else:
            question = (
                "How many debt issuance will be maturing until 2030 for Engie Brazil?"
            )
            print(f"Using example question: {question}")

        # Generate response
        print("Generating response...")
        response = generate_response(question, retriever)

        # Update conversation history
        conversation_history = create_history(conversation_history, question, response)

        # Print the response
        print("\nResponse:")
        print(response)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
