# research/attacks/attack4_resource_exhaustion.py

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import psutil
from research.retrieval.base import get_or_create_collection, embed

# ---------------------------------------------------------------------------
# Adversarial query generators
# ---------------------------------------------------------------------------

def craft_repetition_query(base_query: str, repeat: int = 15) -> str:
    """
    Repeat keywords many times to maximize BM25 and embedding cost.
    e.g. "What is GPT-2?" -> "What is GPT-2? GPT-2 GPT-2 GPT-2 ..."
    """
    words = base_query.split()
    if not words:
        return "repetition " * repeat
    repeated = " ".join(words * repeat)
    return repeated[:2000]  # cap at 2000 chars


def craft_maximum_length_query(topic: str = "language model") -> str:
    """
    Generate a very long, semantically valid query that forces the
    embedding model to process maximum token count.
    """
    filler = (
        f"Please provide a comprehensive, detailed, and thorough explanation of {topic}, "
        f"including all historical context, mathematical formulations, architectural details, "
        f"training procedures, evaluation benchmarks, known limitations, future research directions, "
        f"and comparisons with alternative approaches in the literature. "
    )
    return (filler * 8)[:2000]


def craft_broad_scatter_query() -> str:
    """
    A query with maximally diverse vocabulary — forces the vector search
    to compute distances across the widest possible embedding space.
    """
    return (
        "transformer attention mechanism gradient descent backpropagation "
        "language model tokenization embedding layer normalization dropout "
        "fine-tuning pre-training RLHF reward model policy optimization "
        "retrieval augmented generation vector database semantic search "
        "cosine similarity Euclidean distance approximate nearest neighbor "
        "knowledge base poisoning adversarial robustness hallucination mitigation"
    )


ADVERSARIAL_QUERY_TYPES = {
    "repetition":    craft_repetition_query,
    "max_length":    lambda _: craft_maximum_length_query(),
    "broad_scatter": lambda _: craft_broad_scatter_query(),
}


# ---------------------------------------------------------------------------
# Resource measurement
# ---------------------------------------------------------------------------

def measure_query_resources(
    collection_name: str,
    query: str,
    strategy: str = "topk",
    top_k: int = 3
) -> dict:
    """
    Runs a retrieval query and measures wall-clock time and CPU usage.
    Returns a resource metrics dict.
    """
    process = psutil.Process(os.getpid())

    # Snapshot CPU and memory before
    # Using interval=None for non-blocking cpu percent snapshot
    process.cpu_percent(interval=None)
    mem_before = process.memory_info().rss / (1024 * 1024)  # MB
    start_time = time.perf_counter()

    # --- Run the actual retrieval via rag_service to support chosen strategy ---
    from backend.services.rag_service import retrieve
    chunks, scores = retrieve(query, strategy, top_k, collection_name)
    # ---------------------------------------------------------------------------

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    # Measure cpu percent over a tiny interval (0.01s) or non-blocking to avoid stalling
    # 0.01s interval gives a localized cpu usage reading without slowing down the endpoint too much.
    cpu_usage = process.cpu_percent(interval=0.01)
    mem_after = process.memory_info().rss / (1024 * 1024)  # MB

    # Rough energy proxy: CPU% x time (proportional to Joules on a fixed TDP)
    # TDP_WATTS is approximate for a typical dev laptop CPU (15W)
    TDP_WATTS = 15.0
    energy_joules = (cpu_usage / 100.0) * TDP_WATTS * (elapsed_ms / 1000.0)

    return {
        "query_length_chars": len(query),
        "time_ms": round(elapsed_ms, 2),
        "cpu_percent": round(cpu_usage, 1),
        "memory_mb": round(max(0.0, mem_after - mem_before), 2),
        "energy_joules_estimate": round(energy_joules, 4),
    }


def run_exhaustion_comparison(
    collection_name: str,
    base_query: str,
    adversarial_type: str = "repetition",
    strategy: str = "topk",
    top_k: int = 3
) -> dict:
    """
    Compares resource usage between a normal query and an adversarial one.
    Returns metrics for both so the UI can show amplification factor.
    """
    # Normal query metrics
    normal_metrics = measure_query_resources(collection_name, base_query, strategy, top_k)

    # Generate adversarial query
    gen_fn = ADVERSARIAL_QUERY_TYPES.get(adversarial_type, craft_repetition_query)
    adversarial_query = gen_fn(base_query)
    adversarial_metrics = measure_query_resources(collection_name, adversarial_query, strategy, top_k)

    # Amplification factor (how many times more expensive the adversarial query is)
    time_amplification = adversarial_metrics["time_ms"] / max(normal_metrics["time_ms"], 0.1)

    return {
        "base_query": base_query,
        "adversarial_query": adversarial_query,
        "adversarial_type": adversarial_type,
        "normal": normal_metrics,
        "adversarial": adversarial_metrics,
        "time_amplification_factor": round(time_amplification, 2),
    }
