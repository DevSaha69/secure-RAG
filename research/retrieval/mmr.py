import numpy as np
from retrieval.base import embed, get_or_create_collection

class MMRRetriever:
    def __init__(self, collection_name="gpt2_paper", lambda_param=0.5):
        self.collection = get_or_create_collection(collection_name)
        self.lambda_param = lambda_param

    def retrieve(self, query: str, top_k: int = 3, fetch_k: int = 10):
        """
        Retrieves top_k documents using Maximal Marginal Relevance (MMR).
        First retrieves fetch_k (fetch_k > top_k) candidates, then diversifies them.
        Returns a list of tuples: (document_text, score)
        """
        # Embed the query
        query_vector = embed([query])[0]
        query_vector = np.array(query_vector)
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            query_norm = 1.0

        # Query a larger pool of candidates
        # We need embeddings included to calculate similarity between documents
        results = self.collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=max(fetch_k, top_k),
            include=["documents", "embeddings", "distances"]
        )

        if (
            not results
            or not results.get("documents")
            or not results["documents"][0]
            or not results.get("embeddings")
            or results["embeddings"][0] is None
        ):
            return []

        documents = results["documents"][0]
        embeddings = [np.array(emb) for emb in results["embeddings"][0]]
        
        # Normalize candidate embeddings for cosine similarity
        normalized_embs = []
        for emb in embeddings:
            norm = np.linalg.norm(emb)
            if norm == 0:
                norm = 1.0
            normalized_embs.append(emb / norm)

        # Calculate cosine similarities to the query
        query_similarities = []
        for emb in normalized_embs:
            sim = np.dot(emb, query_vector / query_norm)
            query_similarities.append(float(sim))

        # MMR selection loop
        selected_indices = []
        unselected_indices = list(range(len(documents)))

        # Select the first document (highest similarity to query)
        if unselected_indices:
            first_idx = int(np.argmax(query_similarities))
            selected_indices.append(first_idx)
            unselected_indices.remove(first_idx)

        # Select subsequent documents
        while len(selected_indices) < min(top_k, len(documents)) and unselected_indices:
            best_mmr = -float('inf')
            best_idx = -1

            for candidate_idx in unselected_indices:
                # Compute maximum similarity to already selected documents
                max_sim_to_selected = -1.0
                cand_emb = normalized_embs[candidate_idx]
                
                for sel_idx in selected_indices:
                    sim = np.dot(cand_emb, normalized_embs[sel_idx])
                    if sim > max_sim_to_selected:
                        max_sim_to_selected = float(sim)

                # Compute MMR score
                mmr_score = self.lambda_param * query_similarities[candidate_idx] - (1 - self.lambda_param) * max_sim_to_selected
                
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_idx = candidate_idx

            if best_idx != -1:
                selected_indices.append(best_idx)
                unselected_indices.remove(best_idx)

        # Construct final results: list of (doc, score)
        retrieved = []
        for idx in selected_indices:
            retrieved.append((documents[idx], query_similarities[idx]))

        return retrieved
