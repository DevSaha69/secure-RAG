# research/attacks/attack2_kb_poisoning.py
#
# Attack 2: Knowledge Base Poisoning
# ────────────────────────────────────
# The attacker injects semantically plausible but factually WRONG content.
# Unlike prompt injection (which targets the LLM's instruction-following),
# this targets the RETRIEVAL step — poisoned chunks rank high because
# they are semantically similar to real content.
#
# Real-world parallel: A medical RAG has correct drug dosage documents.
# Attacker injects "The adult dose of Drug X is 500mg" when it's actually 50mg.
# The chunk retrieves normally and the LLM confidently gives wrong advice.

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from research.retrieval.base import get_or_create_collection, embed


# ──────────────────────────────────────────────────────────────────
# Core injection — single false fact
# ──────────────────────────────────────────────────────────────────

def inject_false_fact(
    collection_name: str,
    false_statement: str,
    target_query: str = "",
    source_label: str = "authoritative_reference.pdf",
) -> dict:
    """
    Injects a semantically coherent but factually incorrect chunk.

    Strategy: the chunk is embedded normally. Because it's about the same
    topic as real content, cosine similarity pulls it into the top-k results.

    Parameters
    ----------
    collection_name : str
        Target ChromaDB collection.
    false_statement : str
        The false information to inject. Write it like a real document sentence —
        authoritative tone, no typos, no obvious signs of tampering.
    target_query : str
        Optional — the query this chunk should rank highly for.
        Used only for logging/tracking purposes.
    source_label : str
        Fake source filename shown in metadata (makes it look legitimate).

    Returns
    -------
    dict with: poison_id, false_statement, target_query, collection
    """
    collection = get_or_create_collection(collection_name)
    embedding = embed([false_statement])[0]
    poison_id = f"atk2_{np.random.randint(10**7):07d}"

    collection.add(
        documents=[false_statement],
        embeddings=[embedding],
        ids=[poison_id],
        metadatas=[{
            "source": source_label,
            "attack_type": "kb_poisoning",
            "target_query": target_query,
            "is_poison": True,
        }],
    )

    return {
        "poison_id": poison_id,
        "false_statement": false_statement,
        "target_query": target_query,
        "collection": collection_name,
    }


# ──────────────────────────────────────────────────────────────────
# Measurement — how badly has the KB been corrupted?
# ──────────────────────────────────────────────────────────────────

def measure_poison_retrieval_rank(
    collection_name: str,
    query: str,
    top_k: int = 5,
) -> dict:
    """
    Queries the collection and reports how many poisoned chunks appear in top-k.

    This is your primary attack-success metric for KB poisoning.
    A good attack gets poisoned_count > 0 with high rank (low index).

    Returns
    -------
    dict with:
        total_retrieved    — always equals top_k
        poisoned_count     — how many of top_k are poisoned
        poison_ratio       — poisoned_count / top_k (0.0 to 1.0)
        results            — list of {rank, text, is_poison, distance, source}
    """
    collection = get_or_create_collection(collection_name)
    query_emb = embed([query])[0]

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    ranked = []
    poisoned_count = 0

    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, dists), start=1):
        is_poison = bool(meta) and meta.get("attack_type") == "kb_poisoning"
        if is_poison:
            poisoned_count += 1
        ranked.append({
            "rank": rank,
            "text": doc[:200],
            "is_poison": is_poison,
            "distance": round(dist, 4),
            "source": meta.get("source", "unknown") if meta else "unknown",
        })

    return {
        "total_retrieved": top_k,
        "poisoned_count": poisoned_count,
        "poison_ratio": round(poisoned_count / top_k, 2),
        "results": ranked,
    }


# ──────────────────────────────────────────────────────────────────
# Cleanup — restore the KB to its clean state
# ──────────────────────────────────────────────────────────────────

def cleanup_attack2(collection_name: str) -> int:
    """
    Removes ALL kb_poisoning chunks from the collection.

    Returns
    -------
    int — number of poisoned chunks removed
    """
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
