import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.retrieval.base import get_or_create_collection, embed
import numpy as np

def inject_false_fact(
    collection_name: str,
    false_statement: str,
    source_label: str = "authoritative_source.pdf"
) -> dict:
    """
    Injects semantically plausible but factually wrong content.
    """
    collection = get_or_create_collection(collection_name)
    embedding = embed([false_statement])[0]
    poison_id = f"attack2_poison_{np.random.randint(100000)}"

    collection.add(
        documents=[false_statement],
        embeddings=[embedding],
        ids=[poison_id],
        metadatas=[{
            "source": source_label,
            "attack_type": "kb_poisoning",
            "is_poison": True
        }]
    )
    return {
        "poison_id": poison_id,
        "false_statement": false_statement,
        "collection": collection_name
    }


def measure_poison_retrieval_rank(
    collection_name: str,
    query: str,
    k: int = 5
) -> dict:
    """
    Queries the collection and reports how many poisoned chunks appear in top-k.
    Use this AFTER injecting to measure attack success.
    """
    collection = get_or_create_collection(collection_name)
    query_emb = embed([query])[0]
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=k,
        include=["metadatas", "documents"]
    )
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    poisoned_indices = [
        i for i, m in enumerate(metadatas)
        if m and m.get("is_poison", False)
    ]
    return {
        "total_retrieved": k,
        "poisoned_in_top_k": len(poisoned_indices),
        "poisoned_documents": [documents[i] for i in poisoned_indices]
    }


def cleanup_attack2(collection_name: str) -> int:
    collection = get_or_create_collection(collection_name)
    results = collection.get(include=["metadatas"])
    ids_to_delete = [
        results["ids"][i]
        for i, m in enumerate(results["metadatas"])
        if m and m.get("attack_type") == "kb_poisoning"
    ]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)
