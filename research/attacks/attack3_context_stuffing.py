# research/attacks/attack3_context_stuffing.py

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import numpy as np
from research.retrieval.base import get_or_create_collection, embed

# Noise templates — semantically plausible but factually empty
NOISE_TEMPLATES = [
    "The study of {topic} has advanced significantly in recent years, with researchers exploring new methodologies and frameworks for understanding complex phenomena in this domain.",
    "According to recent literature, {topic} represents a critical area of investigation, with ongoing debates surrounding its theoretical underpinnings and practical applications.",
    "Experts in the field of {topic} have noted that current approaches require further refinement, though consensus remains elusive across different academic communities.",
    "The intersection of {topic} and related disciplines presents unique challenges, necessitating interdisciplinary collaboration and novel analytical methods.",
    "Historical perspectives on {topic} reveal a complex evolution of ideas, with early theories often being revised or superseded by more nuanced contemporary frameworks.",
    "Empirical investigations into {topic} have yielded mixed results, with some studies confirming theoretical predictions while others raise important methodological questions.",
    "The practical implications of {topic} extend beyond academia into industry, policy, and everyday decision-making processes in modern society.",
    "Despite substantial progress, the fundamental questions surrounding {topic} remain open, motivating continued research and theoretical development.",
]

TOPICS = [
    "language modeling", "neural network architectures", "attention mechanisms",
    "transformer-based systems", "natural language processing", "deep learning",
    "generative models", "sequence-to-sequence learning", "unsupervised pre-training",
    "text generation", "information retrieval", "knowledge representation",
    "machine learning optimization", "gradient-based training", "parameter estimation",
]


def generate_noise_chunks(n_chunks: int = 100, seed: int = 42) -> list[str]:
    """Generate n_chunks plausible-sounding but semantically hollow noise chunks."""
    random.seed(seed)
    chunks = []
    for _ in range(n_chunks):
        template = random.choice(NOISE_TEMPLATES)
        topic = random.choice(TOPICS)
        chunk = template.format(topic=topic)
        # Pad to make it look like a real document chunk (varies length naturally)
        extra_topic = random.choice(TOPICS)
        chunk += f" This is particularly relevant in the context of {extra_topic}, where recent developments have opened new avenues for exploration."
        chunks.append(chunk)
    return chunks


def inject_stuffing(
    collection_name: str,
    n_chunks: int = 100,
    seed: int = 42
) -> dict:
    """
    Injects n_chunks noise documents into the ChromaDB collection.
    Returns metadata about what was injected.
    """
    collection = get_or_create_collection(collection_name)
    chunks = generate_noise_chunks(n_chunks, seed)
    embeddings = embed(chunks)

    ids = [f"attack3_stuffing_{i}_{np.random.randint(10000)}" for i in range(n_chunks)]
    metadatas = [{
        "source": "stuffing_attack.txt",
        "attack_type": "context_stuffing",
        "is_poison": True
    } for _ in chunks]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )

    return {
        "chunks_injected": n_chunks,
        "collection": collection_name,
        "sample_chunk": chunks[0]
    }


def measure_stuffing_impact(
    collection_name: str,
    query: str,
    top_k: int = 3
) -> dict:
    """
    After injecting stuffing chunks, query the collection and report
    how many of the top-k results are stuffing noise vs. legitimate chunks.
    """
    collection = get_or_create_collection(collection_name)
    query_emb = embed([query])[0]

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        include=["metadatas", "documents"]
    )

    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    noise_indices = [
        i for i, m in enumerate(metadatas)
        if m and m.get("attack_type") == "context_stuffing"
    ]

    return {
        "total_retrieved": top_k,
        "noise_in_top_k": len(noise_indices),
        "legitimate_in_top_k": top_k - len(noise_indices),
        "noise_documents": [documents[i] for i in noise_indices]
    }


def cleanup_attack3(collection_name: str) -> int:
    """Remove all context stuffing chunks. Returns count removed."""
    collection = get_or_create_collection(collection_name)
    results = collection.get(include=["metadatas"])
    
    # Safely handle missing metadatas list or None metadata elements
    if not results or "ids" not in results or "metadatas" not in results:
        return 0
        
    ids_to_delete = [
        results["ids"][i]
        for i, m in enumerate(results["metadatas"])
        if m and m.get("attack_type") == "context_stuffing"
    ]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)
