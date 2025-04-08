import numpy as np
from sentence_transformers import SentenceTransformer

from base import EmbeddingFunc
from utils import get_device


def get_detailed_instruct(task_description: str, query: str) -> str:
    return f"Instruct: {task_description}\nQuery: {query}"


def get_e5_embedder() -> EmbeddingFunc:
    """
    Create an embedding function using the multilingual-e5-large-instruct model.

    Returns:
        EmbeddingFunc: An embedding function that can be used with the graph storage.
    """
    device = get_device()
    model_name = "intfloat/multilingual-e5-large-instruct"
    model = SentenceTransformer(model_name, device=device)

    def embed_texts(texts: list[str]) -> np.ndarray:
        """
        Embed a list of texts using the E5 model.
        """
        embeddings = model.encode(
            texts, convert_to_tensor=False, normalize_embeddings=True
        )
        return np.array(embeddings)

    # E5 large embedding dimension is 1024
    return EmbeddingFunc(
        embedding_dim=1024,
        max_token_size=512,  # Typical for E5 models
        func=embed_texts,
    )
