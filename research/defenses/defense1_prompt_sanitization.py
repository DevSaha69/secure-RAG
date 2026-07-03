# research/defenses/defense1_prompt_sanitization.py

import re

# Known injection trigger phrases
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"\[system\s+(note|override)\]",
    r"forget\s+everything\s+you\s+were\s+told",
    r"disregard\s+the\s+(user('s)?\s+)?question",
    r"new\s+instruction[s]?:",
    r"you\s+are\s+now\s+in\s+(developer|jailbreak|DAN)\s+mode",
    r"act\s+as\s+(if\s+you\s+are\s+)?a[n]?\s+\w+\s+(without|with no)\s+restrictions",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def is_injected(chunk: str) -> bool:
    """Returns True if the chunk contains a known injection pattern."""
    for pattern in _compiled:
        if pattern.search(chunk):
            return True
    return False


def sanitize_chunks(chunks: list[str]) -> tuple[list[str], int]:
    """
    Filters out chunks containing injection patterns.
    Returns (clean_chunks, n_filtered).
    """
    clean = []
    filtered = 0
    for chunk in chunks:
        if is_injected(chunk):
            filtered += 1
        else:
            clean.append(chunk)
    return clean, filtered
