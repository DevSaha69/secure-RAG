# research/defenses/defense3_collection_health.py

from research.retrieval.base import get_or_create_collection

NOISE_RATIO_ALERT_THRESHOLD = 0.15  # alert if > 15% of chunks are flagged poison


def get_collection_health(collection_name: str) -> dict:
    """
    Returns a health report for the collection:
    - total chunks
    - poison chunks (any attack type)
    - noise ratio
    - health score (0-100, higher is better)
    - alert (bool)
    """
    collection = get_or_create_collection(collection_name)
    results = collection.get(include=["metadatas"])
    
    if not results or "metadatas" not in results or not results["metadatas"]:
        return {
            "total_chunks": 0,
            "poison_chunks": 0,
            "legitimate_chunks": 0,
            "noise_ratio": 0.0,
            "health_score": 100.0,
            "alert": False,
            "alert_threshold": NOISE_RATIO_ALERT_THRESHOLD
        }

    metas = results["metadatas"]
    total = len(metas)

    poison_count = sum(
        1 for m in metas
        if m and m.get("is_poison", False)
    )

    noise_ratio = poison_count / total
    health_score = max(0.0, round((1.0 - noise_ratio) * 100.0, 1))
    alert = noise_ratio > NOISE_RATIO_ALERT_THRESHOLD

    return {
        "total_chunks": total,
        "poison_chunks": poison_count,
        "legitimate_chunks": total - poison_count,
        "noise_ratio": round(noise_ratio, 4),
        "health_score": health_score,
        "alert": alert,
        "alert_threshold": NOISE_RATIO_ALERT_THRESHOLD
    }
