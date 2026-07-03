# research/defenses/defense4_rate_limiter.py

import time
from collections import defaultdict

# --- Query Complexity Scorer ---

MAX_QUERY_LENGTH = 500       # characters
MAX_COMPLEXITY_SCORE = 0.75  # 0.0 = simple, 1.0 = maximally adversarial


def score_query_complexity(query: str) -> dict:
    """
    Scores a query from 0.0 (normal) to 1.0 (maximally adversarial).
    Combines length penalty, repetition ratio, and vocabulary diversity.
    """
    words = query.lower().split()
    if not words:
        return {"score": 0.0, "blocked": False, "reason": None}

    # Length score: penalise relative to max query length
    length_score = min(len(query) / float(MAX_QUERY_LENGTH), 1.0)

    # Repetition score: ratio of repeated words
    unique_words = set(words)
    repetition_score = 1.0 - (len(unique_words) / len(words))

    # Vocabulary diversity score (inverted — low diversity = adversarial)
    diversity_score = len(unique_words) / max(len(words), 1)
    adversarial_diversity = 1.0 - diversity_score

    # Weighted composite
    composite = (
        0.4 * length_score +
        0.4 * repetition_score +
        0.2 * adversarial_diversity
    )
    composite = round(min(composite, 1.0), 3)

    blocked = composite > MAX_COMPLEXITY_SCORE or len(query) > MAX_QUERY_LENGTH
    reason = None
    if len(query) > MAX_QUERY_LENGTH:
        reason = f"Query too long ({len(query)} chars, max {MAX_QUERY_LENGTH})"
    elif composite > MAX_COMPLEXITY_SCORE:
        reason = f"Query complexity score {composite} exceeds threshold {MAX_COMPLEXITY_SCORE}"

    return {
        "score": composite,
        "length_score": round(length_score, 3),
        "repetition_score": round(repetition_score, 3),
        "diversity_score": round(diversity_score, 3),
        "blocked": blocked,
        "reason": reason
    }


# --- In-Memory Rate Limiter ---

_request_log: dict[str, list[float]] = defaultdict(list)

# Modified window and max requests to be dev-friendly (e.g. 60 reqs / min)
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 60


def check_rate_limit(client_ip: str) -> dict:
    """
    Simple sliding-window rate limiter.
    Returns {"allowed": bool, "requests_in_window": int}.
    """
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    # Remove timestamps outside the window
    _request_log[client_ip] = [
        t for t in _request_log[client_ip] if t > window_start
    ]

    count = len(_request_log[client_ip])
    allowed = count < RATE_LIMIT_MAX_REQUESTS

    if allowed:
        _request_log[client_ip].append(now)

    return {
        "allowed": allowed,
        "requests_in_window": count,
        "limit": RATE_LIMIT_MAX_REQUESTS,
        "window_seconds": RATE_LIMIT_WINDOW_SECONDS
    }
