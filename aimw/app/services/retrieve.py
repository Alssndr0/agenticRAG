import json
import pickle
from typing import Any, Dict, Optional

import numpy as np
from app.configs.path_config import get_path_settings
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from loguru import logger


class HybridRetriever:
    def __init__(
        self,
        faiss_index: str = get_path_settings().FAISS_INDEX,
        bm25_index: str = get_path_settings().BM25_INDEX,
        model_embeddings=None,
    ):
        # Use pre-loaded embeddings if provided; otherwise, raise an error.
        if model_embeddings is not None:
            self.model_embeddings = model_embeddings.model.embeddings
            logger.info(f"Using preloaded embedding model: {model_embeddings}")
        else:
            raise ValueError(
                "Either 'embedding_model' or 'model_embeddings' must be provided."
            )

        # Load FAISS index.
        try:
            self.faiss_index = FAISS.load_local(
                faiss_index,
                self.model_embeddings,
                allow_dangerous_deserialization=True,
            )
            logger.info(f"FAISS index loaded from: {faiss_index}")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            raise

        # Load BM25 index and documents.
        try:
            with open(bm25_index, "rb") as f:
                data = pickle.load(f)
                self.bm25 = data["bm25"]
                texts = data["texts"]
                metadata = data["metadata"]
                self.documents = [
                    Document(page_content=text, metadata=meta)
                    for text, meta in zip(texts, metadata)
                ]
            logger.info(f"BM25 index loaded from: {bm25_index}")
        except Exception as e:
            logger.error(f"Error loading BM25 index: {e}")
            raise

    def filter_document_ids(self, filter_dict):
        """Filter documents based on metadata and return matching document IDs."""
        filtered_ids = []
        for doc_id, doc in self.faiss_index.docstore._dict.items():
            metadata = doc.metadata
            if self._matches_filter(metadata, filter_dict):
                filtered_ids.append(doc_id)
        return filtered_ids

    def _matches_filter(self, metadata, filter_dict):
        """Check if a document's metadata matches the filter criteria."""
        if not filter_dict:
            return True  # No filtering applied

        for key, value in filter_dict.items():
            if isinstance(value, list):  # If multiple values are allowed
                if metadata.get(key) not in value:
                    return False
            else:
                if metadata.get(key) != value:
                    return False

        return True

    def optimized_faiss_search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 5,
        fetch_k: int = 100,  # Fetch more results initially
    ):
        """Optimized FAISS search with metadata filtering."""
        if not metadata_filter:
            # Use built-in search if no filtering needed
            try:
                return self.faiss_index.similarity_search_with_score(query, k=k)
            except Exception as e:
                logger.error(f"Error during FAISS search: {e}")
                return []

        # Get vector embedding for the query
        try:
            query_embedding = np.array(
                [self.model_embeddings.embed_query(query)], dtype=np.float32
            )
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            return []

        # Get filtered document IDs
        filtered_ids = self.filter_document_ids(metadata_filter)
        if not filtered_ids:
            logger.info("No documents match the filter criteria")
            return []

        # Get corresponding FAISS indices
        filtered_indices = {
            i for i, doc_id in self.faiss_index.index_to_docstore_id.items()
            if doc_id in filtered_ids
        }

        # Progressive search to ensure we get enough results
        max_attempts = 3
        attempt = 0
        results = []

        while len(results) < k and attempt < max_attempts:
            # Increase fetch_k with each attempt
            current_fetch_k = min(
                fetch_k * (2 ** attempt),
                len(self.faiss_index.index_to_docstore_id)
            )
            
            # Search the FAISS index directly
            try:
                scores, indices = self.faiss_index.index.search(
                    query_embedding, current_fetch_k
                )
            except Exception as e:
                logger.error(f"Error searching FAISS index: {e}")
                break

            # Process results, keeping only those that match our filter
            for i, score in zip(indices[0], scores[0]):
                if i == -1:  # Invalid index
                    continue
                    
                if i in filtered_indices:
                    doc_id = self.faiss_index.index_to_docstore_id[i]
                    doc = self.faiss_index.docstore.search(doc_id)
                    results.append((doc, score))
                    
                    if len(results) >= k:
                        break
            
            attempt += 1
            if current_fetch_k >= len(self.faiss_index.index_to_docstore_id):
                break  # We've searched all documents
                
        return results[:k]

    def search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 5,
        alpha: float = 0.5,
    ):
        """Hybrid search using optimized FAISS and BM25 search."""
        # Determine the number of documents to retrieve from FAISS vs. BM25.
        k_faiss = int(alpha * k)
        k_bm25 = k - k_faiss

        # Handle edge cases: ensure at least one result from each retriever if possible.
        if k_faiss == 0 and alpha > 0:
            k_faiss = 1
            k_bm25 = k - k_faiss
        elif k_bm25 == 0 and alpha < 1:
            k_bm25 = 1
            k_faiss = k - k_bm25

        seen_ids = set()

        # --- Optimized FAISS search ---
        faiss_results = self.optimized_faiss_search(
            query, 
            metadata_filter=metadata_filter,
            k=k_faiss * 2  # Fetch extra to account for potential duplicates
        )

        faiss_docs = []
        for doc, distance in faiss_results:
            doc_id = doc.metadata.get("id")
            if doc_id not in seen_ids:
                faiss_score = 1 / (1 + distance)  # Convert distance to similarity
                faiss_docs.append(
                    {"doc": doc, "score": faiss_score, "retrieval_method": "FAISS"}
                )
                seen_ids.add(doc_id)
            if len(faiss_docs) >= k_faiss:
                break

        # --- BM25 search (with zero score filtering) ---
        tokenized_query = query.split()
        try:
            bm25_scores = self.bm25.get_scores(tokenized_query, metadata_filter=metadata_filter)
        except Exception as e:
            logger.error(f"Error during BM25 search: {e}")
            bm25_scores = np.zeros(len(self.documents))

        # Filter out zero scores for BM25
        non_zero_indices = [(idx, score) for idx, score in enumerate(bm25_scores) if score > 0]
        
        # Sort by score in descending order
        sorted_indices = sorted(non_zero_indices, key=lambda x: x[1], reverse=True)
        
        bm25_docs = []
        for idx, score in sorted_indices:
            if len(bm25_docs) >= k_bm25:
                break
            doc = self.documents[idx]
            doc_id = doc.metadata.get("id")
            if doc_id in seen_ids:
                continue
            bm25_docs.append(
                {"doc": doc, "score": score, "retrieval_method": "BM25"}
            )
            seen_ids.add(doc_id)

        # Combine FAISS and BM25 results
        results_docs = faiss_docs + bm25_docs

        # If we still have fewer than k results, try to fill with more FAISS results
        if len(results_docs) < k and len(faiss_results) > len(faiss_docs):
            for doc, distance in faiss_results:
                if len(results_docs) >= k:
                    break
                doc_id = doc.metadata.get("id")
                if doc_id not in seen_ids:
                    faiss_score = 1 / (1 + distance)
                    results_docs.append(
                        {"doc": doc, "score": faiss_score, "retrieval_method": "FAISS"}
                    )
                    seen_ids.add(doc_id)

        # Prepare the final results
        results = []
        for item in results_docs[:k]:  # Ensure exactly k items
            doc = item["doc"]
            score = item["score"]
            retrieval_method = item["retrieval_method"]
            results.append(
                {
                    "chunk": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score,
                    "retrieval_method": retrieval_method,
                }
            )
        return results
