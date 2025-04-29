import os
import sys
from typing import Any, Dict, List, Optional

# allow module imports when run as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from sentence_transformers import SentenceTransformer
from utils.load_env import get_env_vars

# hybrid retriever with FAISS, BM25 & Neo4j graph
try:
    from hybrid_retriever import HybridRetriever  # script run directly
except ImportError:
    from .hybrid_retriever import HybridRetriever  # module import

# ─── Load config & initialize clients ────────────────────────────────────────
ENV = get_env_vars()

# Validate required env vars
if not ENV.get("OPENAI_API_KEY"):
    raise ValueError("Missing required environment variable: OPENAI_API_KEY")

client = OpenAI(api_key=ENV["OPENAI_API_KEY"])


# ─── Embeddings model ────────────────────────────────────────────────────────
def initialize_embeddings_model(
    model_name: str = ENV["EMBED_MODEL_ID"],
) -> SentenceTransformer:
    try:
        model = SentenceTransformer(model_name)
        print(f"✅ Loaded embeddings model: {model_name}")
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load embeddings model '{model_name}': {e}")


# ─── Retriever factory ───────────────────────────────────────────────────────
def initialize_retriever(
    embeddings_model: Optional[SentenceTransformer] = None,
) -> HybridRetriever:
    """
    Initialize the HybridRetriever. 
    Index paths and Neo4j creds are read from ENV.
    """
    if embeddings_model is None:
        embeddings_model = initialize_embeddings_model()

    return HybridRetriever(
        model_embeddings=embeddings_model
    )


# ─── Response generation ────────────────────────────────────────────────────
def generate_response(
    question: str,
    retriever: HybridRetriever,
    model: str = ENV["OPENAI_MODEL"],
    k: int = int(ENV.get("RETRIEVE_K", 5)),
    alpha: float = float(ENV.get("RETRIEVE_ALPHA", 0.7)),
    include_graph: bool = True,
    graph_ratio: float = float(ENV.get("GRAPH_RATIO", 0.3)),
) -> str:
    """
    1) Hybrid retrieval: graph, FAISS, BM25
    2) Build a unified context
    3) Call OpenAI chat completion
    """
    # fetch
    results = retriever.search(
        query=question,
        metadata_filter=None,
        k=k,
        alpha=alpha,
        include_graph=include_graph,
        graph_ratio=graph_ratio,
    )
    if not results:
        return "No relevant information found."

    # format context
    ctx_parts: List[str] = []
    for item in results:
        method = item["retrieval_method"]
        if method == "graph":
            ent = item["entity"]
            conns = item["connections"]
            # Attributes dict -> inline key: val pairs
            attrs = ", ".join(f"{kk}={vv}" for kk, vv in ent["attributes"].items())
            lines = [
                f"Entity: {ent['name']} (type={ent['type']})",
                f"Attributes: {attrs or 'none'}",
                "Connections:"
            ]
            for conn in conns:
                rel = conn["relationship_type"]
                tgt = conn["related_entity"]
                tgt_name = tgt.get("name", "<unknown>")
                tgt_type = tgt.get("entity_type", "<unknown>")
                strength = conn.get("strength", "")
                lines.append(f"  - ({rel}) → {tgt_name} (type={tgt_type}, strength={strength})")
            ctx_parts.append("\n".join(lines))

        else:  # faiss or bm25
            meta = item["metadata"]
            filename = meta.get("filename", "Unknown")
            pages    = meta.get("pages", "N/A")
            chunk    = item["chunk"]
            ctx_parts.append(
                f"Document: {filename}, Page: {pages}\nContent: {chunk}"
            )

    context = "\n\n---\n\n".join(ctx_parts)
    print(f"📑 Retrieved context:\n{context}\n")

    # build messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that answers questions using only the provided context."
        },
        {
            "role": "user",
            "content": (
                f"Context:\n{context}\n\n"
                f"Question: {question}\n\n"
                f"Please answer using *only* factual info from the context, "
                f"and cite your sources (document name/page or entity)."
            )
        }
    ]

    # call OpenAI
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=int(ENV.get("OPENAI_MAX_TOKENS", 500)),
            temperature=float(ENV.get("OPENAI_TEMPERATURE", 0.0)),
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        err = str(e)
        if "invalid model" in err.lower():
            return (
                f"Error: OpenAI model '{model}' invalid or unavailable.\n"
                f"Available: gpt-3.5-turbo, gpt-4-turbo, gpt-4o-mini."
            )
        return f"Error generating response: {err}"


# ─── CLI entrypoint ─────────────────────────────────────────────────────────
def main():
    embeddings_model = initialize_embeddings_model()
    retriever = initialize_retriever(embeddings_model)

    # simple CLI question
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Question: ")

    print("\n🔍 Generating answer...\n")
    answer = generate_response(question, retriever)
    print("\n💬 Answer:\n")
    print(answer)


if __name__ == "__main__":
    main()
