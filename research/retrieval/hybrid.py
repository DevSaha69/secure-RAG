from retrieval.bm25 import BM25Retriever
from retrieval.base import (
    get_or_create_collection
)


class HybridRetriever:

    def __init__(self, chunks):
        self.chunks = chunks
        self.bm25 = BM25Retriever(chunks)

        self.collection = get_or_create_collection(
            "gpt2_paper"
        )

    def retrieve(self, query, top_k=5):

        bm25_results = self.bm25.retrieve(
            query,
            top_k=top_k
        )

        vector_results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        combined = []

        seen = set()

        for chunk, score in bm25_results:

            if chunk not in seen:
                combined.append(chunk)
                seen.add(chunk)

        for chunk in vector_results["documents"][0]:

            if chunk not in seen:
                combined.append(chunk)
                seen.add(chunk)

        return combined[:top_k]