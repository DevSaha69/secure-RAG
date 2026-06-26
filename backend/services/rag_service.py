# backend/services/rag_service.py

from research.retrieval.topk import TopKRetriever
from research.retrieval.bm25 import BM25Retriever
from research.retrieval.hybrid import HybridRetriever
from research.retrieval.mmr import MMRRetriever
from research.retrieval.base import get_or_create_collection
from research.chunker import chunk_text

# Cache retrievers per collection so we don't rebuild BM25 index every request
_bm25_cache = {}
_hybrid_cache = {}


def _get_all_chunks(collection_name: str) -> list[str]:
    """BM25 and Hybrid need the raw chunk list, not just the vector index."""
    collection = get_or_create_collection(collection_name)
    results = collection.get(include=["documents"])
    return results["documents"]


def retrieve(query: str, strategy: str, top_k: int, collection_name: str):
    """
    Returns (chunks: list[str], scores: list[float])
    Matches the (doc, score) tuple format your retrievers already return.
    """
    strategy = strategy.lower()
    if strategy == "topk":
        retriever = TopKRetriever(collection_name)
        results = retriever.retrieve(query, top_k=top_k)

    elif strategy == "bm25":
        if collection_name not in _bm25_cache:
            chunks = _get_all_chunks(collection_name)
            _bm25_cache[collection_name] = BM25Retriever(chunks)
        results = _bm25_cache[collection_name].retrieve(query, top_k=top_k)

    elif strategy == "hybrid":
        if collection_name not in _hybrid_cache:
            chunks = _get_all_chunks(collection_name)
            _hybrid_cache[collection_name] = HybridRetriever(chunks, collection_name)
        results = _hybrid_cache[collection_name].retrieve(query, top_k=top_k)

    elif strategy == "mmr":
        retriever = MMRRetriever(collection_name)
        results = retriever.retrieve(query, top_k=top_k, fetch_k=top_k * 3)

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    if not results:
        return [], []

    chunks, scores = zip(*results)
    return list(chunks), list(scores)


def invalidate_cache(collection_name: str):
    """Call this after uploading new documents so BM25/Hybrid rebuild their index."""
    _bm25_cache.pop(collection_name, None)
    _hybrid_cache.pop(collection_name, None)
