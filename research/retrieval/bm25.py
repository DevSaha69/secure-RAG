from rank_bm25 import BM25Okapi


class BM25Retriever:

    def __init__(self, chunks):
        self.chunks = chunks

        # Tokenize chunks
        tokenized_chunks = [
            chunk.lower().split()
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(tokenized_chunks)

    def retrieve(self, query, top_k=3):

        tokenized_query = query.lower().split()

        scores = self.bm25.get_scores(
            tokenized_query
        )

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )

        results = []

        for idx in ranked_indices[:top_k]:
            results.append(
                (
                    self.chunks[idx],
                    scores[idx]
                )
            )

        return results