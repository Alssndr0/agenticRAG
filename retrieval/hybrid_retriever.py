import pickle
from typing import Any, Dict, List, Optional

import faiss
import numpy as np


class HybridRetriever:
    """
    A hybrid retrieval system combining FAISS (vector) and BM25 (keyword) search capabilities.

    This retriever allows for flexible document retrieval using both semantic similarity
    and keyword matching approaches, with configurable weighting between the two methods.
    """

    def __init__(
        self,
        faiss_index_path: str,
        bm25_index_path: str,
        model_embeddings: Any = None,
    ):
        """
        Initialize the hybrid retriever with both FAISS and BM25 indexes.

        Args:
            faiss_index_path: Path to the FAISS index file (without extension)
            bm25_index_path: Path to the BM25 index file
            model_embeddings: Model used for embedding queries
        """
        if model_embeddings is None:
            raise ValueError("You must provide a model for embedding.")
        self.model = model_embeddings

        # Load FAISS
        try:
            self.index = faiss.read_index(f"{faiss_index_path}.index")
            with open(f"{faiss_index_path}_meta.pkl", "rb") as f:
                data = pickle.load(f)
                self.texts = data["texts"]
                self.metadata = data["metadata"]
                self.id_map = {i: self.metadata[i] for i in range(len(self.metadata))}
            print(
                f"FAISS index loaded from {faiss_index_path} with {len(self.texts)} documents"
            )
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            raise

        # Load BM25
        try:
            with open(bm25_index_path, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                self.bm25_texts = data["texts"]
                self.bm25_metadata = data["metadata"]
            print(
                f"BM25 index loaded from {bm25_index_path} with {len(self.bm25_texts)} documents"
            )
        except Exception as e:
            print(f"Error loading BM25 index: {e}")
            raise

        # Validate index alignment if possible
        if len(self.texts) != len(self.bm25_texts):
            print(
                f"Warning: FAISS and BM25 indexes have different document counts: {len(self.texts)} vs {len(self.bm25_texts)}"
            )

    def _filter_by_metadata(
        self, metadata_list: List[Dict[str, Any]], filter_dict: Optional[Dict[str, Any]]
    ) -> List[int]:
        """
        Filter documents by their metadata attributes.

        Args:
            metadata_list: List of metadata dictionaries to filter
            filter_dict: Dictionary of key-value pairs to match

        Returns:
            List of indices of documents that match the filter criteria
        """
        if not filter_dict:
            return list(range(len(metadata_list)))

        filtered_ids = []
        for i, meta in enumerate(metadata_list):
            match = all(
                meta.get(k) in v if isinstance(v, list) else meta.get(k) == v
                for k, v in filter_dict.items()
                if k in meta
            )
            if match:
                filtered_ids.append(i)

        return filtered_ids

    def faiss_search(
        self, query: str, metadata_filter: Optional[Dict[str, Any]] = None, k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using FAISS.

        Args:
            query: Search query
            metadata_filter: Optional dictionary for filtering results by metadata
            k: Number of results to return

        Returns:
            List of result dictionaries with chunk, metadata, score, and retrieval method
        """
        instruction = (
            "Given a search query, retrieve relevant passages that answer the query"
        )
        query_embedding = self.model.encode(
            [[instruction, query]], normalize_embeddings=True
        )
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, k * 5)  # over-fetch
        results = []

        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            meta = self.id_map[idx]
            if metadata_filter and not self._filter_by_metadata(
                [meta], metadata_filter
            ):
                continue
            results.append(
                {
                    "chunk": self.texts[idx],
                    "metadata": meta,
                    "score": 1 / (1 + dist),
                    "retrieval_method": "FAISS",
                }
            )

            if len(results) >= k:
                break
        return results

    def bm25_search(
        self, query: str, metadata_filter: Optional[Dict[str, Any]] = None, k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword search using BM25.

        Args:
            query: Search query
            metadata_filter: Optional dictionary for filtering results by metadata
            k: Number of results to return

        Returns:
            List of result dictionaries with chunk, metadata, score, and retrieval method
        """
        tokenized_query = query.split()

        try:
            scores = self.bm25.get_scores(tokenized_query)
        except Exception as e:
            print(f"Error scoring with BM25: {e}")
            return []

        filtered_ids = self._filter_by_metadata(self.bm25_metadata, metadata_filter)
        scored = [(i, scores[i]) for i in filtered_ids if scores[i] > 0]
        scored = sorted(scored, key=lambda x: x[1], reverse=True)[:k]

        return [
            {
                "chunk": self.bm25_texts[i],
                "metadata": self.bm25_metadata[i],
                "score": score,
                "retrieval_method": "BM25",
            }
            for i, score in scored
        ]

    def search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 5,
        alpha: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining FAISS and BM25 results.

        Args:
            query: Search query
            metadata_filter: Optional dictionary for filtering results by metadata
            k: Number of results to return
            alpha: Weight between FAISS and BM25 (1.0 = only FAISS, 0.0 = only BM25)

        Returns:
            List of combined and deduplicated results
        """
        if not (0 <= alpha <= 1):
            raise ValueError("Alpha must be between 0 and 1")

        k_faiss = max(1, int(alpha * k)) if alpha > 0 else 0
        k_bm25 = k - k_faiss if alpha < 1 else 0

        results = []
        seen_ids = set()

        # Get FAISS results
        if k_faiss > 0:
            faiss_results = self.faiss_search(query, metadata_filter, k_faiss)
            for r in faiss_results:
                doc_id = r["metadata"].get("id")
                if doc_id not in seen_ids:
                    results.append(r)
                    seen_ids.add(doc_id)

        # Get BM25 results
        if k_bm25 > 0:
            bm25_results = self.bm25_search(query, metadata_filter, k_bm25)
            for r in bm25_results:
                doc_id = r["metadata"].get("id")
                if doc_id not in seen_ids:
                    results.append(r)
                    seen_ids.add(doc_id)

        # Fill in from FAISS if needed
        if len(results) < k and k_faiss > 0:
            extra_faiss = self.faiss_search(query, metadata_filter, k)
            extra_faiss = [
                r for r in extra_faiss if r["metadata"].get("id") not in seen_ids
            ]
            results.extend(extra_faiss[: k - len(results)])

        # Sort results by score (higher is better)
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        return results[:k]
