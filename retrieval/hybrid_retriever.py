import os
import pickle
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from neo4j import GraphDatabase
from utils.load_env import get_env_vars


class HybridRetriever:
    """
    A context-manager-friendly hybrid retriever combining:
      - FAISS (vector) search
      - BM25 (keyword) search
      - Neo4j graph search (full-text + relationships)
    Configuration (paths, credentials, index names) comes entirely from .env via get_env_vars().
    """

    def __init__(
        self,
        model_embeddings: Any,
        faiss_index_path: Optional[str] = None,
        bm25_index_path: Optional[str] = None,
    ):
        # Load config
        env = get_env_vars()
        faiss_index_path = faiss_index_path or env["FAISS_INDEX_PATH"]
        bm25_index_path = bm25_index_path or env["BM25_INDEX_PATH"]

        # Embedding model
        if model_embeddings is None:
            raise ValueError("An embeddings model must be provided")
        self.model = model_embeddings

        # --- FAISS initialization ---
        try:
            self.index = faiss.read_index(f"{faiss_index_path}.index")
            with open(f"{faiss_index_path}_meta.pkl", "rb") as f:
                data = pickle.load(f)
            self.faiss_texts    = data["texts"]
            self.faiss_metadata = data["metadata"]
            self.id_map         = {i: self.faiss_metadata[i] for i in range(len(self.faiss_metadata))}
            print(f"✅ Loaded FAISS index from {faiss_index_path} ({len(self.faiss_texts)} docs)")
        except Exception as e:
            raise RuntimeError(f"Failed to load FAISS index at {faiss_index_path}: {e}")

        # --- BM25 initialization ---
        try:
            with open(bm25_index_path, "rb") as f:
                data = pickle.load(f)
            self.bm25          = data["bm25"]
            self.bm25_texts    = data["texts"]
            self.bm25_metadata = data["metadata"]
            print(f"✅ Loaded BM25 index from {bm25_index_path} ({len(self.bm25_texts)} docs)")
        except Exception as e:
            raise RuntimeError(f"Failed to load BM25 index at {bm25_index_path}: {e}")

        if len(self.faiss_texts) != len(self.bm25_texts):
            print(
                f"⚠️  FAISS/BM25 size mismatch: {len(self.faiss_texts)} vs. {len(self.bm25_texts)}"
            )

        # --- Neo4j initialization ---
        uri   = env.get("NEO4J_URI")
        user  = env.get("NEO4J_USERNAME")
        pwd   = env.get("NEO4J_PASSWORD")
        self.fulltext_index = env.get("NEO4J_FULLTEXT_INDEX_NAME", "entityNames")
        self.neo4j_driver   = None
        if uri and user and pwd:
            try:
                self.neo4j_driver = GraphDatabase.driver(uri, auth=(user, pwd))
                print(f"✅ Connected to Neo4j at {uri}")
            except Exception as e:
                print(f"⚠️  Neo4j connection failed: {e}")
                self.neo4j_driver = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.neo4j_driver:
            self.neo4j_driver.close()

    # ─── Budget allocation ──────────────────────────────────────────────────────

    @staticmethod
    def _allocate_budget(k: int, alpha: float, graph_ratio: float, include_graph: bool) -> Tuple[int,int,int]:
        """
        Decide how many results to pull from graph, FAISS, and BM25.
        Returns (k_graph, k_faiss, k_bm25).
        """
        k_graph     = int(k * graph_ratio) if include_graph else 0
        remaining   = max(0, k - k_graph)
        k_faiss     = int(round(alpha * remaining)) if alpha > 0 else 0
        k_bm25      = remaining - k_faiss
        return k_graph, k_faiss, k_bm25

    # ─── Result merging ─────────────────────────────────────────────────────────

    @staticmethod
    def _merge_and_dedupe(
        results: List[List[Dict[str, Any]]],
        primary_key: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Flatten multiple lists of result dicts, deduplicate them by a hashable ID,
        sort by descending 'score', and return up to 'limit' items.

        Args:
            results: A list of result lists (e.g. [faiss_results, bm25_results])
            primary_key: The key whose value identifies each result uniquely
                         (e.g. "metadata" for chunks or "entity" for graph nodes)
            limit: Maximum number of items to return

        Returns:
            A list of deduplicated result dicts, sorted by score descending.
        """
        merged: List[Dict[str, Any]] = []
        seen: set = set()

        for result_list in results:
            for item in result_list:
                val = item.get(primary_key)
                # If the value is itself a dict, extract its 'id' field
                if isinstance(val, dict):
                    key = val.get("id")
                else:
                    key = val

                # Skip if no key or already seen
                if key is None or key in seen:
                    continue

                seen.add(key)
                merged.append(item)

        # Sort by score descending and truncate to limit
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged[:limit]

    # ─── Metadata filtering ─────────────────────────────────────────────────────

    @staticmethod
    def _filter_by_metadata(metadata_list: List[Dict[str, Any]], filter_dict: Optional[Dict[str, Any]]) -> List[int]:
        if not filter_dict:
            return list(range(len(metadata_list)))
        filtered = []
        for i, meta in enumerate(metadata_list):
            if all((meta.get(k) in v if isinstance(v, list) else meta.get(k) == v)
                   for k,v in filter_dict.items()):
                filtered.append(i)
        return filtered

    # ─── FAISS search ───────────────────────────────────────────────────────────

    def faiss_search(self, query: str, metadata_filter: Optional[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
        # don’t call FAISS if we have zero budget
        if k <= 0:
           return []
        instruction = "Given a search query, retrieve relevant passages that answer the query"
        emb = self.model.encode([[instruction, query]], normalize_embeddings=True)
        emb = np.array(emb).astype("float32")
        distances, indices = self.index.search(emb, k * 5)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0: continue
            meta = self.id_map[idx]
            if metadata_filter and idx not in self._filter_by_metadata([meta], metadata_filter):
                continue
            score = 1.0 / (1.0 + dist)
            results.append({
                "chunk": self.faiss_texts[idx],
                "metadata": meta,
                "score": score,
                "retrieval_method": "faiss"
            })
            if len(results) >= k:
                break
        return results

    # ─── BM25 search ────────────────────────────────────────────────────────────

    def bm25_search(self, query: str, metadata_filter: Optional[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
        # don’t call BM25 if we have zero budget
        if k <= 0:
           return []
        tokens = query.split()
        try:
            raw_scores = self.bm25.get_scores(tokens)
        except Exception as e:
            print(f"⚠️  BM25 scoring error: {e}")
            return []
        # Normalize to [0,1]
        max_score = max(raw_scores) or 1.0
        normalized = [s / max_score for s in raw_scores]
        filtered_ids = self._filter_by_metadata(self.bm25_metadata, metadata_filter)
        scored = sorted(
            [(i, normalized[i]) for i in filtered_ids if normalized[i] > 0],
            key=lambda x: x[1], reverse=True
        )[:k]
        return [
            {
                "chunk": self.bm25_texts[i],
                "metadata": self.bm25_metadata[i],
                "score": score,
                "retrieval_method": "bm25"
            }
            for i, score in scored
        ]

    # ─── Graph search ───────────────────────────────────────────────────────────

    def graph_search(
        self, 
        query: str, 
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform graph-based search using Neo4j.
        """
        if not self.neo4j_driver or k <= 0:
            return []

        cypher = f"""
        CALL db.index.fulltext.queryNodes($index_name, $q) YIELD node AS e, score
        OPTIONAL MATCH (e)-[r]-(related)
        RETURN e, collect(DISTINCT {{
            relationship: type(r),
            entity: related,
            strength: r.strength
        }}) AS conns, score
        ORDER BY score DESC
        LIMIT $limit
        """

        results = []
        with self.neo4j_driver.session() as sess:
            try:
                records = sess.run(
                    cypher,
                    index_name=self.fulltext_index,  # your index name
                    q=query,                          # renamed param
                    limit=k
                )
                for rec in records:
                    node = rec["e"]
                    conns = rec["conns"]
                    ent = dict(node)
                    results.append({
                        "entity": {
                            "id": ent.get("id"),
                            "name": ent.get("name"),
                            "type": ent.get("entity_type"),
                            "attributes": {
                                kk: vv for kk, vv in ent.items()
                                if kk not in ("id", "name", "entity_type")
                            }
                        },
                        "connections": [
                            {
                                "relationship_type": c["relationship"],
                                "related_entity": dict(c["entity"]),
                                "strength": c["strength"]
                            }
                            for c in conns if c["entity"] is not None
                        ],
                        "score": rec["score"],
                        "retrieval_method": "graph"
                    })
            except Exception as e:
                print(f"⚠️  Neo4j query failed: {e}")

        return results

    # ─── Unified search ─────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 5,
        alpha: float = 0.5,
        include_graph: bool = True,
        graph_ratio: float = 0.3,
    ) -> List[Dict[str, Any]]:
        # Validate
        if not 0 <= alpha <= 1:
            raise ValueError("alpha must be between 0 and 1")
        if not 0 <= graph_ratio <= 1:
            raise ValueError("graph_ratio must be between 0 and 1")

        # Allocate budgets
        k_graph, k_faiss, k_bm25 = self._allocate_budget(k, alpha, graph_ratio, include_graph)

        # Retrieve
        graph_results = self.graph_search(query, metadata_filter, k_graph)
        faiss_results = self.faiss_search(query, metadata_filter, k_faiss)
        bm25_results  = self.bm25_search(query, metadata_filter, k_bm25)

        # Merge + dedupe
        # For graph: dedupe on entity.id; for chunks: dedupe on metadata.id
        merged = []
        if graph_results:
            merged.extend(self._merge_and_dedupe([graph_results], primary_key="entity", limit=k))
        merged.extend(self._merge_and_dedupe([faiss_results, bm25_results], primary_key="metadata", limit=k))

        # Final sort & truncate
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged[:k]

    def close(self):
        """Explicitly close Neo4j driver if not using context manager."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
