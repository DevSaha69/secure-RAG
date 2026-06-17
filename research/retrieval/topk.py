from retrieval.base import embed, get_or_create_collection

class TopKRetriever:
    def __init__(self, collection_name="gpt2_paper"):
        self.collection = get_or_create_collection(collection_name)

    def retrieve(self, query: str, top_k: int = 3):
        """
        Retrieves the top_k most similar documents to the query.
        Returns a list of tuples: (document_text, score)
        where a higher score indicates greater similarity.
        """
        # Embed the query
        query_vector = embed([query])[0]
        
        # Query ChromaDB collection
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )
        
        retrieved = []
        if results and "documents" in results and results["documents"] and len(results["documents"][0]) > 0:
            documents = results["documents"][0]
            distances = results["distances"][0] if "distances" in results and results["distances"] else [1.0] * len(documents)
            
            for doc, dist in zip(documents, distances):
                # Convert distance to a similarity score (higher is better)
                # L2 distance is common. Cosine similarity = 1 - cosine distance.
                # We use 1 / (1 + dist) as a robust distance-to-similarity conversion.
                score = 1.0 / (1.0 + dist)
                retrieved.append((doc, score))
                
        return retrieved
