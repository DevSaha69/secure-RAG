from .bm25 import BM25Retriever
from .topk import TopKRetriever

class HybridRetriever:
    def __init__(self, chunks, collection_name="gpt2_paper", rrf_k=60):
        self.bm25_retriever = BM25Retriever(chunks)
        self.topk_retriever = TopKRetriever(collection_name)
        self.rrf_k = rrf_k

    def retrieve(self, query: str, top_k: int = 3):
        """
        Retrieves top_k documents using Hybrid Retrieval (BM25 + Vector Search) via Reciprocal Rank Fusion (RRF).
        Returns a list of tuples: (document_text, score)
        """
        # Retrieve a slightly larger candidate set from each retriever
        candidate_count = max(top_k * 3, 10)
        
        bm25_results = self.bm25_retriever.retrieve(query, top_k=candidate_count)
        vector_results = self.topk_retriever.retrieve(query, top_k=candidate_count)

        rrf_scores = {}
        doc_map = {}

        # Normalize text keys slightly to merge near-identical strings
        def get_clean_key(text):
            return " ".join(text.split())

        # Process BM25 results (rank 1-indexed)
        for rank, (doc, _) in enumerate(bm25_results, start=1):
            key = get_clean_key(doc)
            doc_map[key] = doc
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.rrf_k + rank))

        # Process Vector results (rank 1-indexed)
        for rank, (doc, _) in enumerate(vector_results, start=1):
            key = get_clean_key(doc)
            doc_map[key] = doc
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.rrf_k + rank))

        # Sort descending by combined RRF score
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        retrieved = []
        for key in sorted_keys[:top_k]:
            retrieved.append((doc_map[key], rrf_scores[key]))

        return retrieved

