import numpy as np
from rank_bm25 import BM25Okapi


class FilteredBM25(BM25Okapi):
    def __init__(self, corpus, metadata):
        """
        Extended BM25Okapi class that supports filtering based on metadata.
        :param corpus: List of tokenized documents.
        :param metadata: List of metadata dictionaries corresponding to each document.
        """
        super().__init__(corpus)
        self.metadata = metadata  # Store metadata alongside documents

    def get_scores(self, query, metadata_filter=None):
        """
        Computes BM25 scores but filters documents based on metadata before scoring.
        :param query: Tokenized query (list of words).
        :param metadata_filter: Dictionary of metadata filters to apply before scoring.
        :return: Scores for documents that pass the filter.
        """
        score = np.zeros(self.corpus_size)
        doc_len = np.array(self.doc_len)

        # Apply metadata filtering before computing scores
        filtered_indices = [
            i
            for i, meta in enumerate(self.metadata)
            if self.matches_filter(meta, metadata_filter)
        ]

        # Compute scores only for filtered documents
        for q in query:
            q_freq = np.array(
                [(self.doc_freqs[i].get(q) or 0) for i in filtered_indices]
            )
            score[filtered_indices] += (self.idf.get(q) or 0) * (
                q_freq
                * (self.k1 + 1)
                / (
                    q_freq
                    + self.k1
                    * (1 - self.b + self.b * doc_len[filtered_indices] / self.avgdl)
                )
            )

        return score

    @staticmethod
    def matches_filter(doc_metadata, metadata_filter):
        """
        Check if a document's metadata matches the given filter criteria.
        :param doc_metadata: Metadata dictionary of a document.
        :param metadata_filter: Dictionary with filter criteria.
        :return: True if the document matches the filter, False otherwise.
        """
        if not metadata_filter:
            return True  # No filtering applied
        for key, value in metadata_filter.items():
            if doc_metadata.get(key) != value:
                return False
        return True
