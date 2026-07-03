# research/defenses/defense2_anomaly_detection.py

import numpy as np
from research.retrieval.base import get_or_create_collection, embed

SIMILARITY_THRESHOLD = 0.92  # chunks more similar than this are flagged


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0


def is_anomalous(
    new_chunk: str,
    new_source: str,
    collection_name: str,
    threshold: float = SIMILARITY_THRESHOLD
) -> dict:
    """
    Check if a new chunk is suspiciously similar to existing chunks
    from a different source — a strong signal of poisoning.

    Returns a dict with 'flagged' (bool) and 'max_similarity' (float).
    """
    collection = get_or_create_collection(collection_name)
    count = collection.count()
    if count == 0:
        return {"flagged": False, "max_similarity": 0.0}

    new_emb = embed([new_chunk])[0]

    # Fetch all existing chunks with their metadata
    existing = collection.get(include=["embeddings", "metadatas"])
    existing_embs = existing["embeddings"]
    existing_metas = existing["metadatas"]

    # If there are no embeddings, return early
    if existing_embs is None or len(existing_embs) == 0:
        return {"flagged": False, "max_similarity": 0.0}

    max_sim = 0.0
    flagged = False

    for emb, meta in zip(existing_embs, existing_metas):
        # Only compare against chunks from a DIFFERENT source
        source = meta.get("source", "") if meta else ""
        if not source or source == new_source:
            continue
        sim = cosine_similarity(new_emb, emb)
        if sim > max_sim:
            max_sim = sim
        if sim > threshold:
            flagged = True
            break  # one hit is enough

    return {
        "flagged": flagged,
        "max_similarity": round(max_sim, 4),
        "threshold": threshold
    }


def scan_collection_for_anomalies(
    collection_name: str,
    threshold: float = SIMILARITY_THRESHOLD
) -> list[dict]:
    """
    Scans the entire collection for suspicious chunks.
    Returns a list of flagged chunk IDs and their max similarity.
    Useful for a periodic audit endpoint.
    """
    collection = get_or_create_collection(collection_name)
    existing = collection.get(include=["embeddings", "metadatas", "documents"])
    
    if not existing or "ids" not in existing or not existing["ids"]:
        return []

    ids = existing["ids"]
    embs = existing["embeddings"]
    metas = existing["metadatas"]
    docs = existing["documents"]

    flagged_chunks = []

    for i, (id_, emb, meta, doc) in enumerate(zip(ids, embs, metas, docs)):
        source_i = meta.get("source", "") if meta else ""
        if not source_i:
            continue
            
        max_sim = 0.0
        for j, (emb2, meta2) in enumerate(zip(embs, metas)):
            if i == j:
                continue
            source_j = meta2.get("source", "") if meta2 else ""
            if not source_j or source_i == source_j:
                continue
            sim = cosine_similarity(emb, emb2)
            if sim > max_sim:
                max_sim = sim

        if max_sim > threshold:
            flagged_chunks.append({
                "id": id_,
                "source": source_i,
                "max_cross_source_similarity": round(max_sim, 4),
                "preview": doc[:100] if doc else ""
            })

    return flagged_chunks
