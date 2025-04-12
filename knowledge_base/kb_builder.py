import importlib
import os
import pickle
from datetime import datetime

import faiss
import numpy as np

from knowledge_base.bm25 import FilteredBM25


class KbBuilder:
    def __init__(self, model):
        self.model = model
        self.index = None
        self.texts = None
        self.metadata = None
        self.id_map = {}

        # BM25 info (optional)
        self.bm25_name = ""
        self.bm25_version = ""
        try:
            self.bm25_name = importlib.metadata.metadata("rank_bm25")["Name"]
            self.bm25_version = importlib.metadata.version("rank_bm25")
        except Exception as e:
            print(f"Error fetching bm25 metadata: {e}")

    def faiss_create_index(self, final_chunks: list[dict]):
        texts = [i["chunk"] for i in final_chunks]
        metadata = [i["metadata"] for i in final_chunks]

        for idx, meta in enumerate(metadata):
            if "id" not in meta:
                meta["id"] = idx

        instruction = (
            "Given a search query, retrieve relevant passages that answer the query"
        )
        inputs = [[instruction, text] for text in texts]
        embeddings = self.model.encode(inputs, normalize_embeddings=True)
        embeddings = np.array(embeddings).astype("float32")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        self.texts = texts
        self.metadata = metadata
        self.id_map = {i: metadata[i] for i in range(len(metadata))}

        return self.index

    def faiss_save_index(self, index_name: str):
        if self.index is None:
            raise ValueError("No FAISS index to save. Create an index first.")
        try:
            index_dir = "indexes/FAISS-TEST"
            os.makedirs(index_dir, exist_ok=True)

            # Save index
            faiss.write_index(
                self.index, os.path.join(index_dir, f"{index_name}.index")
            )

            # Save metadata and texts
            with open(os.path.join(index_dir, f"{index_name}_meta.pkl"), "wb") as f:
                pickle.dump({"texts": self.texts, "metadata": self.metadata}, f)

            print(f"Index saved successfully @ {index_dir}")
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
            raise

    def create_save_faiss_index(self, final_chunks: list[dict], index_name: str):
        self.faiss_create_index(final_chunks)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_name = f"{index_name}_{timestamp}"
        self.faiss_save_index(full_name)

    def faiss_load_index(self, index_path_prefix: str):
        try:
            # Load index
            self.index = faiss.read_index(f"{index_path_prefix}.index")

            # Load metadata and texts
            with open(f"{index_path_prefix}_meta.pkl", "rb") as f:
                data = pickle.load(f)
                self.texts = data["texts"]
                self.metadata = data["metadata"]
                self.id_map = {i: self.metadata[i] for i in range(len(self.metadata))}

            print(f"FAISS index loaded from: {index_path_prefix}")
            return self.index
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            raise

    def faiss_search(self, query: str, top_k: int = 5):
        if self.index is None:
            raise ValueError("FAISS index not loaded.")

        instruction = (
            "Given a search query, retrieve relevant passages that answer the query"
        )
        query_embedding = self.model.encode(
            [[instruction, query]], normalize_embeddings=True
        )
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            results.append(
                {
                    "text": self.texts[idx],
                    "metadata": self.id_map[idx],
                    "distance": float(dist),
                }
            )
        return results

    def bm25_create_index(self, final_chunks: list[dict]):
        texts = [i["chunk"] for i in final_chunks]
        metadata = [i["metadata"] for i in final_chunks]
        for idx, meta in enumerate(metadata):
            if "id" not in meta:
                meta["id"] = idx
        tokenized_corpus = [text.split() for text in texts]
        bm25 = FilteredBM25(tokenized_corpus, metadata)
        self.bm25_index = bm25
        self.texts = texts
        self.metadata = metadata
        return bm25

    def bm25_save_index(self, index_path: str = "indexes/bm25/index.pkl"):
        if self.bm25_index is None:
            raise ValueError("No BM25 index to save. Create an index first.")
        try:
            with open(index_path, "wb") as f:
                pickle.dump(
                    {
                        "bm25": self.bm25_index,
                        "texts": self.texts,
                        "metadata": self.metadata,
                    },
                    f,
                )
            print(f"BM25 index saved successfully @ {index_path}")
        except Exception as e:
            print(f"Error saving BM25 index: {e}")
            raise

    def create_save_bm25_index(
        self, final_chunks: list[dict], index_path: str = "indexes/bm25/"
    ):
        texts = [i["chunk"] for i in final_chunks]
        metadata = [i["metadata"] for i in final_chunks]
        for idx, meta in enumerate(metadata):
            if "id" not in meta:
                meta["id"] = idx
        tokenized_corpus = [text.split() for text in texts]
        bm25 = FilteredBM25(tokenized_corpus, metadata)
        self.bm25_index = bm25
        self.texts = texts
        self.metadata = metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(index_path, exist_ok=True)
        output_path = os.path.join(index_path, f"bm25_index_{timestamp}.pkl")
        try:
            with open(output_path, "wb") as f:
                pickle.dump(
                    {
                        "bm25": self.bm25_index,
                        "texts": self.texts,
                        "metadata": self.metadata,
                    },
                    f,
                )
            print(f"BM25 index created and saved successfully @ {output_path}")
        except Exception as e:
            print(f"Error saving BM25 index: {e}")
            raise

    def load_bm25_index(self, input_path: str):
        try:
            with open(input_path, "rb") as f:
                data = pickle.load(f)
                self.bm25_index = data["bm25"]
                self.texts = data["texts"]
                self.metadata = data["metadata"]
            print(f"BM25 index loaded from: {input_path}")
            return self.bm25_index, self.texts, self.metadata
        except Exception as e:
            print(f"Error loading BM25 index: {e}")
            raise
